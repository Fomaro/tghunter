"""
Performance and Load Testing: 100, 1000, 10000, 50000 names
Measures throughput, RAM usage, and SQLite query speed.
"""
import os
import tempfile
import time
from pathlib import Path

import psutil

from telegram_username_hunter.analysis.scoring import UsernameScorer
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.database.models import UsernameRecord
from telegram_username_hunter.generators.username_generator import UsernameGenerator


def get_current_ram_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def test_generator_throughput_100_names():
    gen = UsernameGenerator()
    t0 = time.perf_counter()
    batch = gen.generate_batch(count=100)
    elapsed = time.perf_counter() - t0

    assert len(batch) == 100
    assert elapsed < 0.2  # Should generate 100 names in < 200ms


def test_generator_throughput_1000_names():
    gen = UsernameGenerator()
    t0 = time.perf_counter()
    batch = gen.generate_batch(count=1000)
    elapsed = time.perf_counter() - t0

    assert len(batch) == 1000
    assert elapsed < 1.0  # Should generate 1000 names in < 1 second


def test_generator_throughput_10000_names():
    gen = UsernameGenerator()
    ram_start = get_current_ram_mb()
    t0 = time.perf_counter()
    batch = gen.generate_batch(count=10000)
    elapsed = time.perf_counter() - t0
    ram_end = get_current_ram_mb()

    assert len(batch) == 10000
    assert elapsed < 8.0  # Fast generation
    assert (ram_end - ram_start) < 150.0  # RAM growth must be bounded


def test_generator_throughput_50000_names():
    gen = UsernameGenerator()
    ram_start = get_current_ram_mb()
    t0 = time.perf_counter()
    batch = gen.generate_batch(count=50000)
    elapsed = time.perf_counter() - t0
    ram_end = get_current_ram_mb()

    assert len(batch) == 50000
    # High throughput: 50,000 unique candidates generated quickly
    assert elapsed < 35.0
    assert (ram_end - ram_start) < 250.0  # No memory leak


def test_scoring_throughput_10000_names():
    scorer = UsernameScorer()
    sample_names = [f"name_{i}x" for i in range(10000)]

    t0 = time.perf_counter()
    for name in sample_names:
        score, _ = scorer.calculate_score(name, category="tech")
        assert 0 <= score <= 100
    elapsed = time.perf_counter() - t0

    # 10,000 scores calculated efficiently (< 5.0s even under profiler / coverage tracing)
    assert elapsed < 5.0


def test_sqlite_batch_operations_performance():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db = DatabaseManager(Path(tmp_dir) / "perf.db")

        # Insert 1,000 records
        t0 = time.perf_counter()
        for i in range(1000):
            db.upsert_username(UsernameRecord(
                username=f"testname_{i}",
                category="5_chars",
                status="AVAILABLE_TO_CLAIM",
                score=75
            ))
        insert_time = time.perf_counter() - t0
        assert insert_time < 15.0  # 1000 individual connection inserts on Windows disk

        # Query and filter
        t0 = time.perf_counter()
        results = db.get_usernames(limit=500, status="AVAILABLE_TO_CLAIM", min_score=70)
        query_time = time.perf_counter() - t0

        assert len(results) == 500
        assert query_time < 0.1  # Fast indexed query < 100ms
