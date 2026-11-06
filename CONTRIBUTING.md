# Contributing to Telegram Username Hunter

Thank you for your interest in contributing to **Telegram Username Hunter**! We welcome bug reports, feature suggestions, and pull requests while maintaining strict code quality, security, and stability standards.

---

## Code of Conduct & Contribution Guidelines

1. **Security First**: Never submit pull requests that include hardcoded API keys, Telegram Bot Tokens, credentials, or personal databases.
2. **Quality Standards**: All contributions must pass the automated test suite, Ruff linting, and Mypy static type checking.
3. **No Breaking Changes**: Core checker and database schemas must maintain backward compatibility.

---

## Development Workflow

### 1. Fork and Clone
1. Fork the repository to your own GitHub account.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/tghunter.git
   cd tghunter
   ```

### 2. Set Up the Environment
Ensure you have **Python 3.12+** installed:
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
pip install ruff mypy pytest pytest-asyncio pytest-cov pyinstaller
```

### 3. Create a Feature Branch
```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/issue-description
```

### 4. Running Tests & Linters
Before pushing any code, verify all quality gates locally:
```bash
# Run Ruff lint check
python -m ruff check telegram_username_hunter/

# Run Mypy static type check
python -m mypy telegram_username_hunter/

# Run full test suite (64 tests)
python -m pytest tests/ -v
```

### 5. Submitting a Pull Request
1. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(generator): add Web3 dictionary category"
   ```
2. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
3. Open a Pull Request against the `main` branch.
4. Fill out the provided Pull Request template completely.
5. Our GitHub Actions CI will automatically run tests and linters on both Windows and Linux environments.

---

## Reporting Issues

- **Bug Reports**: Use our [Bug Report Template](https://github.com/Fomaro/tghunter/issues/new?template=bug_report.yml) and include full logs from `logs/hunter.log`.
- **Feature Requests**: Use our [Feature Request Template](https://github.com/Fomaro/tghunter/issues/new?template=feature_request.yml) to discuss ideas before writing code.
