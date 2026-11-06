"""
Telegram Username Hunter PRO
Comprehensive Performance and Stability Audit Script (Prompt #3)
Tests scaling on 100, 1,000, 10,000, and 50,000 items with memory/CPU profiling,
plus extended continuous load testing to verify zero memory leaks and SQLite integrity.
"""
import asyncio
import gc
import tempfile
import time
from pathlib import Path
import psutil

from telegram_username_hunter.analysis.scoring import UsernameScorer
from telegram_username_hunter.config.settings import (
    AppSettings,
    PerformanceMode,
    UsernameCategory,
    UsernameStatus,
)
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.database.models import UsernameRecord
from telegram_username_hunter.generators.username_generator import UsernameGenerator
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.search_service import SearchService


def profile_generation_and_scoring(counts=[100, 1000, 10000, 50000]):
    print("\n--- 1. GENERATION & SCORING SCALING BENCHMARKS ---")
    gen = UsernameGenerator(seed=12345)
    scorer = UsernameScorer()
    proc = psutil.Process()

    results = []
    for count in counts:
        gc.collect()
        ram_start = proc.memory_info().rss / (1024 * 1024)
        t0 = time.time()
        names = gen.generate_batch(count=count, min_length=5, max_length=12)
        t_gen = max(0.0001, time.time() - t0)
        gen_speed = count / t_gen

        t1 = time.time()
        for name, cat in names:
            scorer.calculate_score(name, category=cat)
        t_score = max(0.0001, time.time() - t1)
        score_speed = count / t_score

        ram_end = proc.memory_info().rss / (1024 * 1024)
        cpu = psutil.cpu_percent(interval=None)

        res = {
            "count": count,
            "gen_time_s": round(t_gen, 4),
            "gen_speed_n_per_s": round(gen_speed, 1),
            "score_time_s": round(t_score, 4),
            "score_speed_n_per_s": round(score_speed, 1),
            "ram_mb": round(ram_end, 1),
            "cpu_pct": round(cpu, 1)
        }
        results.append(res)
        print(f"Count: {count:<6} | Gen: {res['gen_speed_n_per_s']:>9.1f} n/s ({res['gen_time_s']}s) | "
              f"Score: {res['score_speed_n_per_s']:>9.1f} n/s ({res['score_time_s']}s) | RAM: {res['ram_mb']}MB")
    return results


def profile_sqlite_batch_writes(counts=[100, 1000, 5000, 10000]):
    print("\n--- 2. SQLITE WRITE THROUGHPUT & INTEGRITY ---")
    results = []
    proc = psutil.Process()

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "write_bench.db"
        db = DatabaseManager(db_path)

        for count in counts:
            records = [
                UsernameRecord(
                    username=f"perf_{count}_{i}",
                    category="tech",
                    status=UsernameStatus.AVAILABLE_TO_CLAIM.value,
                    score=80 + (i % 20)
                )
                for i in range(count)
            ]
            gc.collect()
            t0 = time.time()
            with db._lock, db._connection_context() as conn:
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT INTO usernames (
                        username, category, status, score, auction_eligibility,
                        fragment_url, generated_at, last_checked_at, check_source, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [
                    (
                        r.username, r.category, r.status, r.score,
                        r.auction_eligibility, r.fragment_url, r.generated_at,
                        r.last_checked_at, r.check_source, r.notes
                    )
                    for r in records
                ])
            t_write = max(0.0001, time.time() - t0)
            write_speed = count / t_write
            ram = proc.memory_info().rss / (1024 * 1024)

            # Integrity check
            with db._connection_context() as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA integrity_check;")
                integ = cursor.fetchone()[0]

            res = {
                "count": count,
                "write_time_s": round(t_write, 4),
                "write_speed_n_per_s": round(write_speed, 1),
                "integrity": integ,
                "ram_mb": round(ram, 1)
            }
            results.append(res)
            print(f"Batch Insert {count:<6}: {res['write_speed_n_per_s']:>9.1f} rec/s ({res['write_time_s']}s) | Integrity: {integ} | RAM: {res['ram_mb']}MB")
    return results


async def profile_extended_stress_load():
    print("\n--- 3. EXTENDED CONTINUOUS STRESS RUN (PIPELINE + MULTI-WORKERS) ---")
    proc = psutil.Process()
    ram_initial = proc.memory_info().rss / (1024 * 1024)

    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "stress.db"
        exp_path = Path(tmp_dir) / "exports"

        settings = AppSettings(
            db_path=db_path,
            exports_dir=exp_path,
            mock_mode=True,
            performance_mode=PerformanceMode.FAST,
            custom_concurrency=6
        )
        db = DatabaseManager(db_path)
        exporter = ExportService(db, exp_path)
        service = SearchService(db, settings, exporter)
        service.rate_limiter.base_delay = 0.002
        service.rate_limiter.jitter = 0.001

        # Run 5 consecutive iterations of 200 items each (1000 items total stress)
        total_items = 0
        t_start = time.time()
        for cycle in range(5):
            print(f"  > Stress Cycle {cycle + 1}/5 (200 items)...")
            await service.run_regular_hunter(count=200, categories=[UsernameCategory.FIVE_CHAR, UsernameCategory.BRAND])
            total_items += 200

        total_elapsed = max(0.001, time.time() - t_start)
        gc.collect()
        ram_final = proc.memory_info().rss / (1024 * 1024)
        ram_delta = ram_final - ram_initial

        with db._connection_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COUNT(DISTINCT username) FROM usernames;")
            count_total, count_distinct = cursor.fetchone()
            cursor.execute("PRAGMA integrity_check;")
            integ = cursor.fetchone()[0]

        print(f"  Finished {total_items} checks in {total_elapsed:.2f}s ({total_items / total_elapsed * 60:.1f} names/min)")
        print(f"  RAM Initial: {ram_initial:.1f}MB -> Final: {ram_final:.1f}MB (Delta: {ram_delta:+.2f}MB)")
        print(f"  DB Rows: {count_total}, Distinct: {count_distinct} (Duplicates: {count_total - count_distinct})")
        print(f"  DB Integrity: {integ}")

        return {
            "total_items": total_items,
            "elapsed_s": round(total_elapsed, 2),
            "speed_per_min": round(total_items / total_elapsed * 60, 1),
            "ram_initial_mb": round(ram_initial, 1),
            "ram_final_mb": round(ram_final, 1),
            "ram_delta_mb": round(ram_delta, 2),
            "duplicates": count_total - count_distinct,
            "integrity": integ
        }


if __name__ == "__main__":
    profile_generation_and_scoring()
    profile_sqlite_batch_writes()
    asyncio.run(profile_extended_stress_load())
