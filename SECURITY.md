# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

---

## Reporting a Vulnerability

Security is a paramount priority for **Telegram Username Hunter**. If you discover a security vulnerability or potential risk:

1. **Do NOT open a public issue.**
2. Send a detailed report directly to the repository maintainer via private message or email at:
   `vinogradov-semen@list.ru`
3. Please include:
   - Type of vulnerability (e.g., rate-limit bypass risk, path traversal, injection).
   - Step-by-step instructions or proof-of-concept to reproduce the behavior.
   - Affected platform and environment.
4. Maintainers will acknowledge receipt within 48 hours and work on a fix promptly.

---

## Compliance & Rate Limiting

This tool adheres strictly to responsible web scraping ethics:
- Respects Telegram `FloodWait` and HTTP `429 Too Many Requests` responses.
- Implements exponential backoff and jittered delays.
- Does **not** bypass Telegram authentication, authorization mechanisms, or platform terms of service.
- Never stores or transmits personal authentication tokens without explicit user configuration.
