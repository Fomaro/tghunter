# Changelog

All notable changes to **Telegram Username Hunter** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-11-06 (Major Release v2)

### Changed
- **Pure Markdown Multi-Category Export System**: Completely eliminated legacy `.csv` and `.txt` file generation. All exported data is now organized strictly into 7 categorized GitHub-Flavored Markdown reports plus a complete master registry:
  - `1_available.md` (Свободные / AVAILABLE)
  - `2_fragment_purchase.md` (Можно купить на Fragment / PURCHASE_AVAILABLE)
  - `3_occupied.md` (Занятые / OCCUPIED)
  - `4_restricted.md` (Ограниченные системной политикой / RESTRICTED)
  - `5_invalid.md` (Недействительные / INVALID)
  - `6_unknown.md` (Не проверено / UNKNOWN)
  - `7_errors.md` (Ошибки проверки / ERROR)
  - `8_all_statuses.md` (Полный реестр всех статусов)
- **Automatic Legacy Cleanup**: Automatic removal of old `.csv` and `.txt` files from `exports/` folder when exports are triggered, keeping workspace directories clean and organized.
- **Direct Link Previews & Code Blocks**: All reports feature clickable hyperlinks to `t.me/<username>` and `fragment.com/username/<username>`, structured markdown tables, and batch `@username` code blocks ready for instant copy-pasting.
- **Optimized Dependencies**: Removed Pandas from active export flow, utilizing lightweight native formatting for maximal export speed and zero memory overhead.

### Fixed
- **Export Clutter**: Addressed user-reported clutter where CSV and TXT files were generated alongside Markdown files.

## [1.0.3] - 2026-11-06

### Added
- **Structured Markdown (.md) Multi-Category Export System**: Export engine now generates 7 dedicated Markdown reports matching all status categories from the selector plus errors and full registry:
  - `1_available.md` (Свободные / AVAILABLE)
  - `2_fragment_purchase.md` (Можно купить на Fragment / PURCHASE_AVAILABLE)
  - `3_occupied.md` (Занятые / OCCUPIED)
  - `4_restricted.md` (Ограниченные системной политикой / RESTRICTED)
  - `5_invalid.md` (Недействительные / INVALID)
  - `6_unknown.md` (Не проверено / UNKNOWN)
  - `7_errors.md` (Ошибки проверки / ERROR)
  - `8_all_statuses.md` (Полный реестр всех статусов)
- **Interactive Markdown Features**: Each `.md` report contains rich GitHub-flavored markdown tables with clickable links to Telegram profiles (`t.me/<name>`) and Fragment pages (`fragment.com/username/<name>`), detailed status breakdowns, scores, lengths, and a dedicated quick-copy block (`@username`) for batch workflows.
- **Automatic Folder Opening**: UI export triggers now automatically open the `exports/` folder in the OS file manager upon completion.

### Fixed
- **Selective Export Limitations**: Fixed previous export behavior that only generated plain `.txt` and `.csv` files for high-score names, enabling complete categorization for all statuses and error tracking.

## [1.0.2] - 2026-11-06

### Added
- **MTProto Protocol Definitions & Specification Checkers**: Integrated official Telegram MTProto specifications (`account.checkUsername`, `contacts.resolveUsername`, `channels.checkUsername`).
- **Independent Two-Component Status Taxonomy**: Strict separation between **Availability Status** (`AVAILABLE`, `OCCUPIED`, `INVALID`, `RESTRICTED`, `UNKNOWN`, `ERROR`) and **Fragment Status** (`AUCTION_SUPPORTED`, `AUCTION_NOT_SUPPORTED`, `PURCHASE_AVAILABLE`, `AUCTION_UNKNOWN`).
- **Telegram Policy Word Blacklist**: Server-level protected dictionary words and anti-squatting handles (`viper`, `amber`, `cloud`, `admin`, etc.) that trigger `USERNAME_INVALID` in MTProto are mapped to `RESTRICTED`.
- **4-Character Handle Specialization**: 4-char handles (`shop`, `game`) recognized as Fragment Collectibles (`RESTRICTED` + `PURCHASE_AVAILABLE`), preventing false claim attempts on standard user accounts.
- **Dual Status Filter in UI**: Added separate dropdown filters for Availability Status and Fragment Status in "Premium Selection" table.
- **Comprehensive Availability Test Suite**: 12 automated unit and integration tests (`tests/test_username_availability.py`) covering all MTProto RPC responses and regression verifying 0% false positives.
- **Audit Documentation**: Detailed root cause analysis and Telegram MTProto behavior specification published in `USERNAME_AVAILABILITY_AUDIT.md`.

### Fixed
- **`viper` False Positive Regression**: Fixed false `AVAILABLE` reporting for `viper` and other empty `t.me` profiles where MTProto returns `USERNAME_INVALID`.
- **Unconfirmed Web 404 Availability Assumption**: The absence of a public profile on `t.me` without MTProto verification now returns `UNKNOWN` instead of `AVAILABLE`.
- **UI Table Status Formatting**: Localized Russian and English status rendering in GUI tables and exports.

## [1.0.1] - 2026-11-06

### Added
- **Startup Update Check**: Automated non-blocking check on application launch against GitHub Releases API with notification banner and direct download button.
- **Manual Update Check**: Dedicated "Check for Updates" button in Settings panel.
- **Telegram Direct Open Action**: Instant `📱 Open in Telegram` button in Premium Selection to verify username status directly in the Telegram client.
- **System Reserved Handles List**: Built-in protection against false-positive availability for system reserved words (`cloud`, `admin`, `support`, etc.).

### Fixed
- **Network Glitch False Errors**: Added 2-attempt retry loop with exponential backoff on transient timeouts/errors in all checkers (`escrowcap` and others).
- **Fragment Taken Status Parsing**: Fixed CSS badge priority in FragmentChecker (`tm-status-taken`, `tm-status-unavail`) preventing occupied/taken names (`zarsyr`, `cloud`, etc.) from falsely appearing as available.
- **Premium Selection Verification Warning**: Added clear disclaimer noting that usernames with blank t.me profiles might belong to private accounts or be reserved.

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
