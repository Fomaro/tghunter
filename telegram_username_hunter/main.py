"""
Telegram Username Hunter PRO
Main Application Entry Point
"""
import logging
import sys

from telegram_username_hunter.config.settings import LOGS_DIR
from telegram_username_hunter.gui import HunterApp


def setup_logging():
    log_file = LOGS_DIR / "hunter.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ]
    )
    logging.info("Telegram Username Hunter PRO initialized.")


def main():
    setup_logging()
    app = HunterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
