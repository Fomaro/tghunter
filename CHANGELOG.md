# Changelog

All notable changes to **Telegram Username Hunter** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-06

### Added
- **Modern Dark UI**: Comprehensive CustomTkinter desktop interface with sidebar navigation (Dashboard, Username Hunter, Bot Hunter, Premium Bots, Selection, Auction Potential, History, Settings).
- **Multi-Category Generators**:
  - Regular usernames (5, 6, 7, 8, 9-12 chars, English dictionary, Finance, Crypto, IT/Tech).
  - Bot usernames with valid Telegram suffixes (`bot`, `_bot`).
  - Premium bot aliases (3-4 char short names, VIP brand prefixes/suffixes).
- **Valuation & Scoring Engine**: Algorithmic scoring (0–100) based on length, pronounceability, vowel harmony, keyword relevance, and Telegram market demand.
- **Fragment TON Auction Analyzer**: Seamless parsing of Fragment marketplace lots, current bids, buy-out prices, and historical sales.
- **Three Performance Modes**:
  - **Economy**: Minimal CPU/RAM usage, low concurrency, extended intervals.
  - **Standard**: Balanced throughput and resource consumption.
  - **Fast**: High-concurrency worker pool with automated flood-wait backoff.
- **Multilingual Support**: Real-time language switching between Russian and English.
- **Data Persistence & Export**: SQLite WAL storage with parameterized queries and instant CSV / TXT exports.
- **Windows Packaging**: Portable standalone single-file EXE (`TelegramUsernameHunter_Portable.exe`) and Inno Setup installer (`TelegramUsernameHunter_Setup_v1.0.0.exe`).
- **Linux Packaging**: Debian `.deb` package and portable AppImage automation scripts.
- **Continuous Integration**: GitHub Actions automated linting, typing, and cross-platform matrix testing on Windows & Linux.

### Fixed
- Fixed false `ERROR` classification for free usernames caused by Fragment HTTP 302 redirects and generic Telegram DOM buttons.
- Fixed directory resolution in PyInstaller builds so database and export folders stay adjacent to the executable.
- Resolved Windows NTFS file connection latency in SQLite batch operations.
