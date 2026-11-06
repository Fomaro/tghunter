"""
GUI Integration Tests: Navigation, View Switching, and Component Wiring
"""
import tempfile
from pathlib import Path

import pytest

from telegram_username_hunter.config.settings import AppSettings
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.gui import HunterApp


@pytest.fixture(scope="module")
def gui_app():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "gui_test.db"
        exp_path = Path(tmp_dir) / "exports"
        settings = AppSettings(
            db_path=db_path,
            exports_dir=exp_path,
            mock_mode=True,
            language="ru"
        )
        db = DatabaseManager(db_path)
        app = HunterApp(db=db, settings=settings)
        app.withdraw()
        yield app, db, settings
        try:
            app.destroy()
        except Exception:
            pass


def test_gui_all_views_instantiated(gui_app):
    app, db, settings = gui_app

    expected_views = [
        "Dashboard",
        "Username Hunter",
        "Bot Username Hunter",
        "Premium Bot Names",
        "Premium Selection",
        "Bot Selection",
        "Auction Potential",
        "History",
        "Settings",
    ]

    for view_name in expected_views:
        assert view_name in app.views
        frame = app.views[view_name]
        assert frame is not None


def test_gui_navigation_switches_views(gui_app):
    app, db, settings = gui_app

    # Test navigating to each section
    for view_name in app.views.keys():
        app.navigate_to(view_name)
        # Active button should be styled as active
        btn = app.nav_buttons.get(view_name)
        assert btn is not None


def test_gui_ui_update_callbacks(gui_app):
    app, db, settings = gui_app

    # Simulate checking item callback
    test_item = {
        "username": "qevro",
        "category": "5_chars",
        "status": "AVAILABLE_TO_CLAIM",
        "score": 85,
        "auction_eligibility": "AUCTION_NOT_SUPPORTED",
        "target_type": "REGULAR"
    }

    app._handle_item_ui_update(test_item)
    hunter_view = app.views["Username Hunter"]
    # Check that item is inserted into table
    children = hunter_view.tree.get_children()
    assert len(children) >= 1

    # Simulate progress callback
    app._handle_progress_ui_update(checked=10, total=100, speed=5.0, available=2, errors=0)
    expected_prog = f"{app._t('metric_progress')}: 10 / 100"
    assert hunter_view.prog_label.cget("text") == expected_prog
    assert "5.0" in hunter_view.speed_label.cget("text")
    assert "2" in hunter_view.avail_label.cget("text")


def test_gui_language_switching_and_persistence(gui_app):
    app, db, settings = gui_app

    # 1. Switch to English
    app.set_language("en")
    assert app.settings.language == "en"
    assert db.get_setting("language") == "en"

    # Verify English UI text
    assert app.title() == "Telegram Username Hunter PRO v2.5"
    assert "Settings" in app.nav_buttons["Settings"].cget("text")
    assert "Dashboard" in app.nav_buttons["Dashboard"].cget("text")
    assert "Username Hunter" in app.nav_buttons["Username Hunter"].cget("text")
    assert "Bot Username Hunter" in app.nav_buttons["Bot Username Hunter"].cget("text")
    assert "Premium Bot Names" in app.nav_buttons["Premium Bot Names"].cget("text")
    assert "🏷 Auction Potential" in app.nav_buttons["Auction Potential"].cget("text")
    assert "Telegram Username Hunter" in app.views["Username Hunter"].lbl_title.cget("text")

    dash_view = app.views["Dashboard"]
    assert "Hunt Usernames" in dash_view.btn_hunt_un.cget("text")
    assert "Hunt Bot Names" in dash_view.btn_hunt_bot.cget("text")
    assert "Hunt Premium Aliases" in dash_view.btn_hunt_alias.cget("text")
    assert "View Premium Selection" in dash_view.btn_view_selection.cget("text")

    settings_view = app.views["Settings"]
    assert settings_view.lbl_lang.cget("text") == "Interface Language:"
    assert settings_view.lang_combo.get() == "English (Английский)"
    assert settings_view.btn_save.cget("text") == "💾 Save Settings"

    # 2. Switch to Russian
    app.set_language("ru")
    assert app.settings.language == "ru"
    assert db.get_setting("language") == "ru"

    # Verify Russian UI text
    assert "Настройки" in app.nav_buttons["Settings"].cget("text")
    assert "Панель управления" in app.nav_buttons["Dashboard"].cget("text")
    assert "Поиск юзернеймов" in app.nav_buttons["Username Hunter"].cget("text")
    assert "Поиск ботов" in app.nav_buttons["Bot Username Hunter"].cget("text")
    assert "Премиум имена ботов" in app.nav_buttons["Premium Bot Names"].cget("text")
    assert "🏷 Аукционный потенциал" in app.nav_buttons["Auction Potential"].cget("text")

    assert "Поиск юзернеймов" in dash_view.btn_hunt_un.cget("text")
    assert "Поиск ботов" in dash_view.btn_hunt_bot.cget("text")
    assert "Премиум имена ботов" in dash_view.btn_hunt_alias.cget("text")
    assert "Премиум отбор" in dash_view.btn_view_selection.cget("text")

    assert settings_view.lbl_lang.cget("text") == "Язык интерфейса:"
    assert settings_view.lang_combo.get() == "Русский (Russian)"
    assert settings_view.btn_save.cget("text") == "💾 Сохранить настройки"
