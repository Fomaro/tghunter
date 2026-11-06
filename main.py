"""
Telegram Username Hunter PRO
Root launcher
"""
import sys
import os

# Ensure package is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from telegram_username_hunter.main import main

if __name__ == "__main__":
    main()
