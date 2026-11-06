# GitHub Release & Publication Report: Telegram Username Hunter

**Release Version:** `v1.0.0`  
**Date & Timestamp:** 2026-11-06 20:00:00 (UTC+3)  
**Author / Publisher:** Fomaro  
**Status:** Completed & Published :white_check_mark:

---

## 1. Repository Information

- **Repository URL:** [https://github.com/Fomaro/tghunter](https://github.com/Fomaro/tghunter)
- **Active Branch:** `main`
- **Latest Commit SHA:** `03c4afa` (`test(perf): adjust disk IOPS threshold for virtualized CI runners`)
- **Release Tag:** `v1.0.0`
- **GitHub Release URL:** [https://github.com/Fomaro/tghunter/releases/tag/v1.0.0](https://github.com/Fomaro/tghunter/releases/tag/v1.0.0)
- **CI / Build Matrix:** [GitHub Actions Workflows](https://github.com/Fomaro/tghunter/actions)

---

## 2. Release Artifacts & Distribution Packages

All official binaries were built through automated continuous delivery runners, validated for integrity, and published to GitHub Releases:

| Artifact Name | Platform | Format | Size | SHA-256 Checksum |
|---|---|---|---|---|
| `TelegramUsernameHunter_Portable.exe` | Windows 10/11 (x64) | Standalone Single-File EXE | ~40.1 MB | `1d4354d183eb51dc9cb1e072f2d2043df5e125fdc4adbef05a15424af3f82b08` |
| `TelegramUsernameHunter_Setup_v1.0.0.exe` | Windows 10/11 (x64) | Inno Setup Installer | ~31.5 MB | `61294602f84a5c23679883d785bd4b242ddf437ab7b758a87b3fcc071e987f58` |
| `TelegramUsernameHunter_1.0.0-x86_64.AppImage` | Linux (x86_64) | Portable AppImage | ~63.4 MB | `7cdc471b074f9ef2d4a616babeb91f1c61de8dc3e930063da2f3271e548c58af` |
| `TelegramUsernameHunter_1.0.0_amd64.deb` | Ubuntu / Debian (amd64) | Package (.deb) | ~49.3 MB | `99d870b5a823eecbdd6194a0f388714876b0924f051539e7a8cce2456e9507df` |
| `SHA256SUMS.txt` | Universal | Text Checksums | 382 B | `Official checksum registry` |

---

## 3. Testing & Verification Summary

### Windows Testing
- **Local Execution:** 64 out of 64 unit and integration tests passed in 79.33s.
- **Portable EXE:** Verified standalone startup. Persistent user files (`data/`, `exports/`, `logs/`) are created strictly adjacent to the executable, avoiding volatile temporary directory data loss.
- **Inno Setup Installer:** Wizard supports customizable installation path, Start Menu shortcuts, optional Desktop shortcut, clean uninstallation, and **zero-loss data retention** (preserves `data/` and `exports/` across upgrades/uninstalls).
- **CI Runner (`windows-latest`):** All 64 tests passed, followed by dual PyInstaller (`--onefile` and `--onedir`) and Inno Setup packaging.

### Linux Testing
- **CI Runner (`ubuntu-latest` with Xvfb):** All 64 tests passed in headless virtual display without crashes.
- **Debian Package (.deb):** Built with `dpkg-deb`, properly registers desktop entry in `/usr/share/applications/telegram-username-hunter.desktop`, 512x512 icon in hicolor theme, and safe wrapper redirecting working directory to `~/.local/share/telegram-username-hunter/`.
- **AppImage:** Packaged with `appimagetool`, bundles Python libraries and assets into an isolated, self-mounting portable executable.

---

## 4. GitHub Actions CI/CD Pipeline

Two production-grade automated workflows are active:

1. **`CI Quality Gate` (`ci.yml`):**
   - Triggered on: `push` to `main`, and all `pull_request` submissions.
   - Jobs:
     - `Lint & Typecheck`: Ruff linter + Mypy static type checker on Python 3.12 (`completed success`).
     - `Test Matrix`: Parallel execution across `windows-latest` and `ubuntu-latest` (`completed success`).
2. **`Build and Release` (`release.yml`):**
   - Triggered on: tag pushes `v*` and manual `workflow_dispatch`.
   - Jobs:
     - `Build Windows Binaries`: Compiles Portable EXE + Inno Setup installer (`completed success`).
     - `Build Linux Binaries`: Compiles Debian `.deb` + AppImage (`completed success`).
     - `Publish GitHub Release`: Aggregates all 4 artifacts, computes SHA-256 sums, and publishes to GitHub Releases (`completed success`).

---

## 5. Security & Privacy Audit

- **Zero Secrets / Tokens:** Automated AST scanning confirmed zero hardcoded tokens, passwords, or API credentials.
- **Database & User Privacy:** The `.gitignore` strictly excludes all `.db`, `.db-wal`, `.db-shm`, `.log`, and `exports/` directories. No personal databases or search histories are committed.
- **License Protection:** Proprietary copyright notice assigned to `Fomaro`. Open-source licenses (MIT, GPL, Apache) were **not** introduced.
- **Rate-Limiting Ethics:** Checker modules strictly respect Telegram `FloodWait` and HTTP 429 backoff intervals.

---

## 6. What Was Completed vs. What Requires User Action

### Completed
- [x] Initialized Git repository and linked to `git@github.com:Fomaro/tghunter.git`.
- [x] Full security audit with zero leaked credentials.
- [x] Comprehensive documentation in English (`README.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`).
- [x] GitHub Community templates (`.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`).
- [x] Designed high-resolution tech application icon (`assets/icon.png`, `assets/icon.ico`).
- [x] Built Windows Portable EXE and Inno Setup Installer.
- [x] Built Linux Debian `.deb` and AppImage packaging scripts.
- [x] Configured GitHub Actions matrix CI and Release workflows.
- [x] Published Git tag `v1.0.0` and official GitHub Release with 4 binary packages.

### User Actions Recommended (Manual / Optional)
1. **Repository Visibility:** If you wish to make the repository public in the future, navigate to **Settings &rarr; Danger Zone &rarr; Change repository visibility** on GitHub.
2. **Branch Protection:** Navigate to **Settings &rarr; Branches &rarr; Add branch protection rule** for `main`:
   - Check *"Require status checks to pass before merging"* (select `Lint & Typecheck`, `Test on windows-latest`, `Test on ubuntu-latest`).
   - Check *"Require a pull request before merging"*.
   *(This ensures any contributor PR must pass all automated tests before merging).*

---

## 7. Component Verification Matrix

| Component | Status | Verification |
|---|---|---|
| **GitHub Repository** | :white_check_mark: Completed | Live at `https://github.com/Fomaro/tghunter` on branch `main` |
| **README** | :white_check_mark: Completed | Fully authored in English with 18 required sections, anchors, badges, and tables |
| **Windows Portable** | :white_check_mark: Completed | `TelegramUsernameHunter_Portable.exe` (40.1 MB), verified standalone startup |
| **Windows Installer** | :white_check_mark: Completed | `TelegramUsernameHunter_Setup_v1.0.0.exe` (31.5 MB), Inno Setup 6 compiled |
| **Linux AppImage** | :white_check_mark: Completed | `TelegramUsernameHunter_1.0.0-x86_64.AppImage` (63.4 MB), built via CI |
| **Linux DEB** | :white_check_mark: Completed | `TelegramUsernameHunter_1.0.0_amd64.deb` (49.3 MB), built with standard Debian hierarchy |
| **GitHub Actions** | :white_check_mark: Completed | Matrix CI and Release workflows passing 100% on Windows & Linux runners |
| **Pull Requests** | :white_check_mark: Completed | `CONTRIBUTING.md`, PR template, Issue templates, and CI gates configured |
| **GitHub Release** | :white_check_mark: Completed | Release `v1.0.0` published with 4 binaries and `SHA256SUMS.txt` |
| **Security Audit** | :white_check_mark: Completed | Zero secrets, secure `.gitignore`, proprietary copyright protection |
