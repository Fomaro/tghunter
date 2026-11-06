"""
Telegram Username Hunter PRO
Empirical Performance Benchmark Script
Runs Economy, Standard, and Fast modes with real rate-limits/profiles
to capture precise comparative metrics for PERFORMANCE_TEST_REPORT.md.
"""
import asyncio
import os
import time
import tempfile
from pathlib import Path
import psutil

from telegram_username_hunter.config.settings import (
    AppSettings,
    PerformanceMode,
    PERFORMANCE_PROFILES,
    UsernameCategory,
)
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.search_service import SearchService


async def benchmark_single_mode(mode: PerformanceMode, custom_concurrency=None, sample_count: int = 15):
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / f"bench_{mode.value}.db"
        exp_path = Path(tmp_dir) / "exports"

        settings = AppSettings(
            db_path=db_path,
            exports_dir=exp_path,
            mock_mode=True,
            performance_mode=mode,
            custom_concurrency=custom_concurrency
        )
        db = DatabaseManager(db_path)
        exporter = ExportService(db, exp_path)
        service = SearchService(db, settings, exporter)
        service.set_performance_mode(mode, custom_concurrency=custom_concurrency)

        proc = psutil.Process()
        # Prime CPU measurement
        psutil.cpu_percent(interval=None)

        start_time = time.time()
        start_ram = proc.memory_info().rss / (1024 * 1024)

        cpu_samples = []
        ram_samples = []
        workers_samples = []

        async def telemetry_collector():
            while service.is_running:
                cpu_samples.append(psutil.cpu_percent(interval=None))
                ram_samples.append(proc.memory_info().rss / (1024 * 1024))
                workers_samples.append(service.active_workers_count)
                await asyncio.sleep(0.2)

        collector_task = asyncio.create_task(telemetry_collector())

        await service.run_regular_hunter(count=sample_count, categories=[UsernameCategory.FIVE_CHAR])

        elapsed = max(0.001, time.time() - start_time)
        service.is_running = False
        await collector_task

        speed_n_per_min = (sample_count / elapsed) * 60.0
        avg_cpu = sum(cpu_samples) / max(1, len(cpu_samples))
        peak_ram = max(ram_samples) if ram_samples else start_ram
        avg_workers = sum(workers_samples) / max(1, len(workers_samples))

        profile = settings.get_active_profile()

        return {
            "mode": mode.value,
            "mode_name_ru": profile.name_ru,
            "concurrency": profile.concurrency,
            "base_delay": profile.request_delay_seconds,
            "batch_delay": profile.batch_delay_seconds,
            "elapsed_s": round(elapsed, 2),
            "sample_count": sample_count,
            "speed_per_min": round(speed_n_per_min, 1),
            "avg_cpu_pct": round(avg_cpu, 1),
            "peak_ram_mb": round(peak_ram, 1),
            "avg_workers": round(avg_workers, 1),
            "errors": service._error_count,
        }


async def main():
    print("================ RUNNING EMPIRICAL BENCHMARKS ================")
    results = []
    # Test Economy (delay 2.2s, 1 worker, 8 names)
    print("Testing Economy Mode...")
    eco = await benchmark_single_mode(PerformanceMode.ECONOMY, sample_count=8)
    results.append(eco)

    # Test Standard (delay 1.2s, 3 workers, 12 names)
    print("Testing Standard Mode...")
    std = await benchmark_single_mode(PerformanceMode.STANDARD, sample_count=12)
    results.append(std)

    # Test Fast (delay 0.5s, 6 workers, 18 names)
    print("Testing Fast Mode...")
    fst = await benchmark_single_mode(PerformanceMode.FAST, custom_concurrency=6, sample_count=18)
    results.append(fst)

    print("\n================ BENCHMARK RESULTS ================")
    print(f"{'Mode':<12} | {'Concurrency':<12} | {'Delay(s)':<8} | {'Speed(n/min)':<14} | {'CPU(%)':<8} | {'RAM(MB)':<10} | {'Errors':<6}")
    print("-" * 80)
    for r in results:
        print(f"{r['mode_name_ru']:<12} | {r['concurrency']:<12} | {r['base_delay']:<8} | {r['speed_per_min']:<14} | {r['avg_cpu_pct']:<8} | {r['peak_ram_mb']:<10} | {r['errors']:<6}")


if __name__ == "__main__":
    asyncio.run(main())
