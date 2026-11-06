# Telegram Username Hunter

[![CI Quality Gate](https://github.com/Fomaro/tghunter/actions/workflows/ci.yml/badge.svg)](https://github.com/Fomaro/tghunter/actions/workflows/ci.yml)
[![Build and Release](https://github.com/Fomaro/tghunter/actions/workflows/release.yml/badge.svg)](https://github.com/Fomaro/tghunter/actions/workflows/release.yml)
[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/Fomaro/tghunter)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)
[![Latest Release](https://img.shields.io/badge/release-v1.0.2-emerald.svg)](https://github.com/Fomaro/tghunter/releases)

A high-performance desktop application for automated discovery, availability verification, valuation scoring, and auction monitoring of Telegram usernames, bot handles, and premium aliases. Built with Python 3.12, CustomTkinter, Asyncio, and SQLite WAL mode.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Interface Overview](#interface-overview)
- [System Requirements](#system-requirements)
- [Supported Operating Systems](#supported-operating-systems)
- [Installation](#installation)
  - [Windows Portable (.exe)](#windows-portable-exe)
  - [Windows Installer (.exe)](#windows-installer-exe)
  - [Linux AppImage](#linux-appimage)
  - [Linux Debian / Ubuntu (.deb)](#linux-debian--ubuntu-deb)
- [Quick Start](#quick-start)
- [Performance Modes](#performance-modes)
- [Username Categories](#username-categories)
- [Database and Export](#database-and-export)
- [Configuration](#configuration)
- [Building from Source](#building-from-source)
- [Troubleshooting](#troubleshooting)
- [Security and Privacy](#security-and-privacy)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

---

## Overview

**Telegram Username Hunter** helps domainers, collectors, and developers discover unregistered high-value Telegram handles and analyze existing Fragment TON auctions. It features a modern dark-themed graphical user interface, intelligent multi-dictionary generation, adaptive rate-limiting, and an automated valuation engine.

---

## Key Features

- **Multi-Source Availability Checking**: Real-time validation via `t.me` web endpoints and Fragment TON auction detection without blind redirect collisions.
- **Three-Engine Generator**:
  - Regular Telegram usernames (5–12 characters, dictionary words, Crypto, Finance, IT/Tech).
  - Bot usernames with strict Telegram naming rules (`bot`, `_bot` suffixes).
  - Short 3–4 letter premium bot aliases and brandable short-codes.
- **Valuation & Scoring Engine**: Heuristic multi-factor scoring (0–100) analyzing length, syllable harmony, dictionary presence, pronounceability, and commercial value.
- **Fragment Auction Potential**: Identifies active auctions, buyout prices, and Toncoin valuation metrics.
- **Adaptive Performance Management**: 3 selectable performance modes (Economy, Standard, Fast) dynamically throttling requests upon encountering `FloodWait` or HTTP 429.
- **Bilingual Interface**: Seamless on-the-fly switching between English and Russian.
- **Persistent Local Database**: High-speed SQLite database with Write-Ahead Logging (WAL) and indexed lookups.
- **One-Click Export**: Export filtered results to CSV (compatible with Excel/Pandas) or clean TXT lists.

---

## Interface Overview

The application features a sleek dark-mode UI with sidebar navigation:

| View | Purpose |
|---|---|
| **Dashboard** | Real-time counters: total generated, checked, free usernames, free bots, error rates, and latest activity. |
| **Username Hunter** | Filterable generation and live availability checking for standard user accounts. |
| **Bot Username Hunter** | Specialized search for available bot names with proper suffixes. |
| **Premium Bot Names** | Dedicated search for scarce 3–4 letter bot handles and VIP prefixes. |
| **Premium Selection** | Curated catalog of high-scoring usernames (Score ≥ 70). |
| **Bot Selection** | Curated catalog of available high-value bot usernames. |
| **Auction Potential** | Telegram handles currently in auction on Fragment with TON pricing data. |
| **History** | Searchable audit trail of all previous lookups with instant CSV/TXT export. |
| **Settings** | Concurrency limits, request delays, language selection (EN/RU), and quick export folder access. |

> **Note on Screenshots**: When running in automated CI environments or headless Windows sessions, GUI window capture is omitted to maintain authentic presentation rather than synthetic mockups. Full UI layout and responsive controls are rendered natively by CustomTkinter.

---

## System Requirements

- **Processor**: 64-bit Dual-Core x86_64 processor or better.
- **RAM**: Minimum 512 MB available RAM (1 GB recommended for Fast mode).
- **Disk Space**: ~150 MB free space (including binaries and database storage).
- **Network**: Active broadband Internet connection with HTTPS access to `t.me` and `fragment.com`.

---

## Supported Operating Systems

| Operating System | Architecture | Supported Formats |
|---|---|---|
| **Windows 11** | 64-bit (x64) | Portable Standalone EXE, Inno Setup Installer |
| **Windows 10** | 64-bit (x64) | Portable Standalone EXE, Inno Setup Installer |
| **Ubuntu 20.04+ / Debian 11+** | 64-bit (amd64) | Standalone AppImage, Debian (.deb) Package |
| **Other Linux Distributions** | 64-bit (x86_64) | Standalone AppImage, Source execution |

---

## Installation

### Windows Portable (.exe)
No installation or Python runtime required.
1. Download `TelegramUsernameHunter_Portable.exe` from [Releases](https://github.com/Fomaro/tghunter/releases).
2. Place the executable in any folder of your choice.
3. Double-click to launch. All application data (`data/`, `exports/`, `logs/`) will be stored directly beside the `.exe`.

### Windows Installer (.exe)
1. Download `TelegramUsernameHunter_Setup_v1.0.0.exe` from [Releases](https://github.com/Fomaro/tghunter/releases).
2. Run the installer wizard.
3. Choose installation path (default: `C:\Program Files\Telegram Username Hunter`) and optionally create Desktop and Start Menu shortcuts.
4. *Upgrading or uninstalling will never delete your existing database or exported files.*

### Linux AppImage
1. Download `TelegramUsernameHunter_1.0.0-x86_64.AppImage` from [Releases](https://github.com/Fomaro/tghunter/releases).
2. Make it executable:
   ```bash
   chmod +x TelegramUsernameHunter_1.0.0-x86_64.AppImage
   ```
3. Run the AppImage:
   ```bash
   ./TelegramUsernameHunter_1.0.0-x86_64.AppImage
   ```

### Linux Debian / Ubuntu (.deb)
1. Download `TelegramUsernameHunter_1.0.0_amd64.deb`.
2. Install via package manager:
   ```bash
   sudo dpkg -i TelegramUsernameHunter_1.0.0_amd64.deb
   # Or with apt:
   sudo apt-get install ./TelegramUsernameHunter_1.0.0_amd64.deb
   ```
3. Launch from your application menu or run `telegram-username-hunter` in your terminal.

---

## Quick Start

1. Launch the application.
2. Navigate to **Username Hunter** from the left navigation bar.
3. Select your desired generator category (e.g., `5_chars`, `crypto`, `english_words`).
4. Set the batch size (e.g., `50`).
5. Click **Start Search**.
6. Real-time results will populate the table. Usernames marked **AVAILABLE TO CLAIM** can be immediately registered directly inside Telegram or via Fragment!
7. Click **Export CSV** to save results for spreadsheet analysis.

---

## Performance Modes

Configure performance modes dynamically in the **Settings** view or during active execution:

| Mode | Parallel Workers | Request Interval | Memory Usage | Target Use Case |
|---|---|---|---|---|
| **Economy** | 1–2 | 1.5s – 3.0s | Low (< 80 MB) | Background scanning, low-spec PCs, strict ISP rate limits. |
| **Standard** *(Default)* | 3–5 | 0.8s – 1.5s | Moderate (< 140 MB) | Balanced daily usage with minimal risk of temporary IP blocks. |
| **Fast** | 6–10 | 0.3s – 0.7s | High (< 220 MB) | Maximum throughput for short bursts. Automatically backs off if 429 occurs. |

---

## Username Categories

The generator supports granular classification rules:

- **5 Characters**: Rare, scarce 5-letter permutations (consonant-vowel harmonic sequences).
- **6 Characters / 7 Characters / 8 Characters**: Mid-tier pronounceable handles.
- **9–12 Characters**: Extended brandable keywords.
- **English Dictionary**: Filtered list of recognized English nouns, adjectives, and verbs.
- **Crypto & Web3**: Curated terms (e.g., `ton`, `node`, `vault`, `swap`, `stake`).
- **Finance & FinTech**: Banking and financial terms (`pay`, `fund`, `ledger`, `broker`).
- **IT & Technology**: Developer keywords (`stack`, `cloud`, `proxy`, `cyber`).
- **Bot Names**: Handles ending in `bot` or `_bot` conforming to Telegram API rules.
- **Premium Bot Aliases**: Scarce 3–4 character bot handles.

---

## Database and Export

- **Storage Engine**: SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and `synchronous=NORMAL` to guarantee zero database locks during rapid concurrent checks.
- **Parameterization**: All queries strictly utilize parameterized SQL statements to eliminate injection vulnerabilities.
- **Exports**:
  - **CSV**: Contains username, category, status, valuation score, TON estimate, checked timestamp.
  - **TXT**: Plain clean newline-separated lists of free handles for direct batch registration.

---

## Configuration

Settings are stored locally in `settings.json` (or configured via the GUI Settings tab):

```json
{
  "performance_mode": "standard",
  "language": "ru",
  "request_timeout": 5.0,
  "max_retries": 3,
  "export_format": "csv"
}
```

---

## Building from Source

### Prerequisites
- Python 3.12+ (64-bit)
- Git

### Setup
```bash
# 1. Clone the repository
git clone https://github.com/Fomaro/tghunter.git
cd tghunter

# 2. Create virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install pyinstaller pytest pytest-asyncio ruff mypy
```

### Running Tests
```bash
# Run all 64 automated tests
python -m pytest tests/ -v
```

### Building Windows Executable
```bash
# Builds portable onefile and installer directory
python build_windows_exe.py
```

---

## Troubleshooting

### Q: Why did a username show as `ERROR`?
- **Cause**: Network timeout or transient connectivity glitch to Telegram or Fragment.
- **Resolution**: Telegram Username Hunter automatically retries up to 3 times with exponential backoff. If the server is unreachable, verify your internet connection.

### Q: Does the application use Telegram User API or Bot Tokens?
- **Answer**: No bot tokens or Telegram user credentials are required. The scanner operates via public HTTP verification endpoints, meaning your personal Telegram account is never exposed to ban risks.

### Q: What happens if Telegram responds with HTTP 429?
- **Answer**: The application automatically intercepts `429 Too Many Requests` or `FloodWait`, pauses execution gracefully, and switches to exponential backoff until the cooldown window expires.

---

## Security and Privacy

- **No Remote Telemetry**: Zero external tracking, telemetry, or user analytics.
- **No Stored Credentials**: No Telegram passwords, session strings, or API secrets are stored or queried.
- **Local Storage**: All databases and logs remain strictly on your local machine.

---

## Contributing

Please review [CONTRIBUTING.md](CONTRIBUTING.md) for pull request guidelines, coding standards, and branch policies.

---

## License

This software and its source code are **Proprietary**. Copyright &copy; 2026 Fomaro. All rights reserved. See [LICENSE](LICENSE) for terms.

---

## Disclaimer

This software is an independent analytical tool and is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Telegram FZ-LLC, Fragment, or the TON Foundation.

Telegram Username Hunter makes **no guarantee** of username availability or perpetual ownership. Username registration is subject entirely to Telegram's terms of service and Fragment auction rules. Use responsibly and adhere to rate limits.
