"""
Telegram Username Hunter PRO
CustomTkinter Desktop GUI Application
Supports dynamic English/Russian language localization, performance modes, and real-time telemetry.
"""
import asyncio
import logging
import os
import threading
import webbrowser
from tkinter import messagebox, ttk
from typing import Any

import customtkinter as ctk

from telegram_username_hunter.analysis.market_analysis import MarketPotentialAnalyzer
from telegram_username_hunter.config.i18n import tr
from telegram_username_hunter.config.settings import (
    DEFAULT_SETTINGS,
    AppSettings,
    BotStatus,
    PerformanceMode,
    PremiumBotStatus,
    UsernameStatus,
)
from telegram_username_hunter.dashboard import DashboardView
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.services.export_service import ExportService
from telegram_username_hunter.services.search_service import SearchService

logger = logging.getLogger(__name__)

# Dark theme palette
BG_DARK = "#0f172a"
PANEL_DARK = "#1e222d"
CARD_DARK = "#262c3a"
ACCENT_BLUE = "#3b82f6"
ACCENT_GREEN = "#10b981"
ACCENT_AMBER = "#f59e0b"
ACCENT_RED = "#ef4444"
TEXT_WHITE = "#f8fafc"
TEXT_MUTED = "#94a3b8"


class BackgroundWorker:
    """Dedicated asyncio worker thread for non-blocking search execution."""

    def __init__(self):
        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def submit(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)


class HunterApp(ctk.CTk):
    """Main Application Window."""

    def __init__(self, db: DatabaseManager | None = None, settings: AppSettings | None = None):
        super().__init__()

        # Core Services
        self.settings = settings or DEFAULT_SETTINGS
        self.db = db or DatabaseManager(self.settings.db_path)

        # Load persisted language preference if present in database
        saved_lang = self.db.get_setting("language", self.settings.language)
        if saved_lang in ("ru", "en"):
            self.settings.language = saved_lang

        self.title(self._t("app_title"))
        self.geometry("1280x820")
        self.minsize(1050, 680)

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG_DARK)

        self.export_service = ExportService(self.db, self.settings.exports_dir)
        self.search_service = SearchService(self.db, self.settings, self.export_service)
        self._active_hunter_type = "REGULAR"

        # Wire up search callbacks
        self.search_service.on_item_checked = self._on_item_checked_callback
        self.search_service.on_progress = self._on_progress_callback
        self.search_service.on_log = self._on_log_callback

        self.worker = BackgroundWorker()

        # Layout Setup: Left Sidebar (Fixed) + Right Content Frame (Dynamic)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._init_sidebar()
        self._init_content_area()

        # Apply initial language localization across all views
        self._apply_language()

        # Telemetry timer
        self.after(1000, self._telemetry_tick)

        # Default View
        self.navigate_to("Dashboard")

    def _t(self, key: str, default: str | None = None) -> str:
        """Helper to get translated string for current language."""
        return tr(key, lang=self.settings.language, default=default)

    def _mode_to_str(self, mode: PerformanceMode) -> str:
        """Convert PerformanceMode enum to localized string."""
        if self.settings.language == "en":
            return {
                PerformanceMode.ECONOMY: "Economy",
                PerformanceMode.STANDARD: "Standard",
                PerformanceMode.FAST: "Fast",
            }.get(mode, "Standard")
        return {
            PerformanceMode.ECONOMY: "Экономный",
            PerformanceMode.STANDARD: "Обычный",
            PerformanceMode.FAST: "Быстрый",
        }.get(mode, "Обычный")

    def _str_to_mode(self, text: str) -> PerformanceMode:
        """Convert localized or standard mode string to PerformanceMode enum."""
        return {
            "Economy": PerformanceMode.ECONOMY,
            "Экономный": PerformanceMode.ECONOMY,
            "Standard": PerformanceMode.STANDARD,
            "Обычный": PerformanceMode.STANDARD,
            "Fast": PerformanceMode.FAST,
            "Быстрый": PerformanceMode.FAST,
        }.get(text, PerformanceMode.STANDARD)

    # ================= SIDEBAR & NAVIGATION =================

    def _init_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=240, fg_color=PANEL_DARK, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Brand Logo / App Title
        brand_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        brand_frame.pack(fill="x", padx=16, pady=(20, 15))

        self.brand_title_lbl = ctk.CTkLabel(
            brand_frame,
            text=self._t("brand_title"),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_WHITE,
        )
        self.brand_title_lbl.pack(anchor="w")

        self.brand_sub_lbl = ctk.CTkLabel(
            brand_frame,
            text=self._t("brand_subtitle"),
            font=ctk.CTkFont(size=11),
            text_color=TEXT_MUTED,
        )
        self.brand_sub_lbl.pack(anchor="w")

        # Nav Buttons Container
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.nav_items_meta = [
            ("Dashboard", "nav_dashboard", "📊"),
            ("Username Hunter", "nav_username_hunter", "🎯"),
            ("Bot Username Hunter", "nav_bot_hunter", "🤖"),
            ("Premium Bot Names", "nav_premium_bot", "✨"),
            ("Premium Selection", "nav_premium_selection", "💎"),
            ("Bot Selection", "nav_bot_selection", "⭐"),
            ("Auction Potential", "nav_auction_potential", "🏷"),
            ("History", "nav_history", "📜"),
            ("Settings", "nav_settings", "⚙"),
        ]

        for name, i18n_key, icon in self.nav_items_meta:
            clean_icon = icon.replace("\ufe0f", "")
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{clean_icon} {self._t(i18n_key)}",
                anchor="w",
                height=40,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="transparent",
                text_color=TEXT_MUTED,
                hover_color=CARD_DARK,
                command=lambda n=name: self.navigate_to(n),
            )
            btn.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[name] = btn

        # Bottom System Info & Telemetry Badge
        bot_frame = ctk.CTkFrame(self.sidebar, fg_color=CARD_DARK, corner_radius=8)
        bot_frame.pack(side="bottom", fill="x", padx=12, pady=12)

        mode_text = self._t("badge_safe_rate_limits") if not self.settings.mock_mode else self._t("badge_mock_mode")
        self.mode_badge = ctk.CTkLabel(
            bot_frame,
            text=mode_text,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#34d399" if not self.settings.mock_mode else "#fbbf24",
        )
        self.mode_badge.pack(anchor="w", padx=8, pady=(6, 2))

        self.telemetry_lbl = ctk.CTkLabel(
            bot_frame,
            text="⚡ Loading...\nRAM: 0.0 MB | CPU: 0%\n" + self._t("status_normal"),
            font=ctk.CTkFont(size=10),
            text_color="#94a3b8",
            justify="left",
        )
        self.telemetry_lbl.pack(anchor="w", padx=8, pady=(0, 6))

    def _init_content_area(self):
        self.content_container = ctk.CTkFrame(self, fg_color="transparent")
        self.content_container.grid(row=0, column=1, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)
        self.content_container.grid_rowconfigure(0, weight=1)

        self.views: dict[str, Any] = {
            "Dashboard": DashboardView(self.content_container, self.db, on_navigate=self.navigate_to),
            "Username Hunter": self._create_hunter_view("REGULAR"),
            "Bot Username Hunter": self._create_hunter_view("BOT"),
            "Premium Bot Names": self._create_hunter_view("PREMIUM_BOT"),
            "Premium Selection": self._create_selection_view(),
            "Bot Selection": self._create_bot_selection_view(),
            "Auction Potential": self._create_auction_view(),
            "History": self._create_history_view(),
            "Settings": self._create_settings_view(),
        }

    def navigate_to(self, view_name: str):
        """Switch active view frame and highlight button."""
        for name, btn in self.nav_buttons.items():
            if name == view_name:
                btn.configure(fg_color="#2563eb", text_color=TEXT_WHITE)
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_MUTED)

        for name, frame in self.views.items():
            if name == view_name:
                frame.grid(row=0, column=0, sticky="nsew")
                if hasattr(frame, "refresh_stats"):
                    frame.refresh_stats()
                elif hasattr(frame, "refresh_data"):
                    frame.refresh_data()
            else:
                frame.grid_forget()

    # ================= LANGUAGE SWITCHING & DYNAMIC TRANSLATION =================

    def set_language(self, lang: str) -> None:
        """Update active language and propagate changes across all UI views."""
        if lang not in ("ru", "en"):
            lang = "ru"
        self.settings.language = lang
        self.db.save_setting("language", lang)
        self._apply_language()

    def _on_language_combo_selected(self, choice: str) -> None:
        """Dropdown handler for language selection in Settings view."""
        chosen_lang = "ru" if "Рус" in choice or "ru" in choice.lower() else "en"
        self.set_language(chosen_lang)

    def _apply_language(self) -> None:
        """Dynamically update all visible text in window, sidebar, and subviews."""
        lang = self.settings.language
        is_ru = (lang == "ru")

        # Window title
        self.title(self._t("app_title"))

        # Sidebar Brand
        if hasattr(self, "brand_title_lbl") and self.brand_title_lbl.winfo_exists():
            self.brand_title_lbl.configure(text=self._t("brand_title"))
        if hasattr(self, "brand_sub_lbl") and self.brand_sub_lbl.winfo_exists():
            self.brand_sub_lbl.configure(text=self._t("brand_subtitle"))

        # Sidebar Navigation Buttons
        if hasattr(self, "nav_items_meta"):
            for name, i18n_key, icon in self.nav_items_meta:
                btn = self.nav_buttons.get(name)
                if btn and btn.winfo_exists():
                    clean_icon = icon.replace("\ufe0f", "")
                    btn.configure(text=f"{clean_icon} {self._t(i18n_key)}")

        # Sidebar Badges
        if hasattr(self, "mode_badge") and self.mode_badge.winfo_exists():
            mode_text = self._t("badge_safe_rate_limits") if not self.settings.mock_mode else self._t("badge_mock_mode")
            self.mode_badge.configure(text=mode_text)

        # Dashboard View
        dash = self.views.get("Dashboard")
        if dash and hasattr(dash, "apply_language"):
            dash.apply_language(lang)

        # Hunter Views (Regular, Bot, Premium Bot)
        hunter_views = [
            ("Username Hunter", "title_regular"),
            ("Bot Username Hunter", "title_bot"),
            ("Premium Bot Names", "title_premium_bot"),
        ]
        mode_vals = ["Экономный", "Обычный", "Быстрый"] if is_ru else ["Economy", "Standard", "Fast"]

        for vname, tkey in hunter_views:
            v = self.views.get(vname)
            if v:
                if hasattr(v, "lbl_title") and v.lbl_title.winfo_exists():
                    v.lbl_title.configure(text=self._t(tkey))
                if hasattr(v, "lbl_count") and v.lbl_count.winfo_exists():
                    v.lbl_count.configure(text=self._t("label_generate_count"))
                if hasattr(v, "lbl_mode") and v.lbl_mode.winfo_exists():
                    v.lbl_mode.configure(text=self._t("label_mode"))
                if hasattr(v, "lbl_workers") and v.lbl_workers.winfo_exists():
                    v.lbl_workers.configure(text=self._t("label_workers"))
                if hasattr(v, "btn_start") and v.btn_start.winfo_exists():
                    v.btn_start.configure(text=self._t("btn_start"))
                if hasattr(v, "btn_pause") and v.btn_pause.winfo_exists():
                    v.btn_pause.configure(text=self._t("btn_pause"))
                if hasattr(v, "btn_resume") and v.btn_resume.winfo_exists():
                    v.btn_resume.configure(text=self._t("btn_resume"))
                if hasattr(v, "btn_stop") and v.btn_stop.winfo_exists():
                    v.btn_stop.configure(text=self._t("btn_stop"))
                if hasattr(v, "btn_export") and v.btn_export.winfo_exists():
                    v.btn_export.configure(text=self._t("btn_export"))
                if hasattr(v, "mode_combo") and v.mode_combo.winfo_exists():
                    v.mode_combo.configure(values=mode_vals)
                    v.mode_combo.set(self._mode_to_str(self.settings.performance_mode))
                if hasattr(v, "throttle_label") and v.throttle_label.winfo_exists() and not self.search_service.rate_limiter.is_throttled:
                    v.throttle_label.configure(text=self._t("status_normal"))
                if hasattr(v, "tree"):
                    col_map = {
                        "username": self._t("col_username"),
                        "length": self._t("col_length"),
                        "category": self._t("col_category"),
                        "status": self._t("col_status"),
                        "score": self._t("col_score"),
                        "auction": self._t("col_auction"),
                        "checked_at": self._t("col_checked_at"),
                    }
                    for col, col_title in col_map.items():
                        v.tree.heading(col, text=col_title)

        # Settings View
        set_view = self.views.get("Settings")
        if set_view:
            if hasattr(set_view, "lbl_title") and set_view.lbl_title.winfo_exists():
                set_view.lbl_title.configure(text=self._t("title_settings"))
            if hasattr(set_view, "lbl_lang") and set_view.lbl_lang.winfo_exists():
                set_view.lbl_lang.configure(text=self._t("label_language"))
            if hasattr(set_view, "lang_combo") and set_view.lang_combo.winfo_exists():
                set_view.lang_combo.set("Русский (Russian)" if is_ru else "English (Английский)")
            if hasattr(set_view, "lbl_mode") and set_view.lbl_mode.winfo_exists():
                set_view.lbl_mode.configure(text=self._t("label_perf_mode"))
            if hasattr(set_view, "mode_opt") and set_view.mode_opt.winfo_exists():
                set_view.mode_opt.configure(values=mode_vals)
                set_view.mode_opt.set(self._mode_to_str(self.settings.performance_mode))
            if hasattr(set_view, "lbl_workers") and set_view.lbl_workers.winfo_exists():
                set_view.lbl_workers.configure(text=self._t("label_parallel_workers"))
            if hasattr(set_view, "lbl_delay") and set_view.lbl_delay.winfo_exists():
                set_view.lbl_delay.configure(text=self._t("label_req_delay"))
            if hasattr(set_view, "lbl_batch") and set_view.lbl_batch.winfo_exists():
                set_view.lbl_batch.configure(text=self._t("label_batch_size"))
            if hasattr(set_view, "lbl_score") and set_view.lbl_score.winfo_exists():
                set_view.lbl_score.configure(text=self._t("label_min_score_thresh"))
            if hasattr(set_view, "mock_check") and set_view.mock_check.winfo_exists():
                set_view.mock_check.configure(text=self._t("check_mock_mode"))
            if hasattr(set_view, "save_check") and set_view.save_check.winfo_exists():
                set_view.save_check.configure(text=self._t("check_auto_save"))
            if hasattr(set_view, "btn_save") and set_view.btn_save.winfo_exists():
                set_view.btn_save.configure(text=self._t("btn_save_settings"))
            if hasattr(set_view, "btn_clear_db") and set_view.btn_clear_db.winfo_exists():
                set_view.btn_clear_db.configure(text=self._t("btn_reset_db"))
            if hasattr(set_view, "btn_open_exp") and set_view.btn_open_exp.winfo_exists():
                set_view.btn_open_exp.configure(text=self._t("btn_open_exports"))

        # Premium Selection View
        ps_view = self.views.get("Premium Selection")
        if ps_view:
            if hasattr(ps_view, "lbl_title") and ps_view.lbl_title.winfo_exists():
                ps_view.lbl_title.configure(text=self._t("title_premium_selection"))
            if hasattr(ps_view, "lbl_min_score") and ps_view.lbl_min_score.winfo_exists():
                ps_view.lbl_min_score.configure(text=self._t("label_min_score"))
            if hasattr(ps_view, "lbl_sort_by") and ps_view.lbl_sort_by.winfo_exists():
                ps_view.lbl_sort_by.configure(text=self._t("label_sort_by"))
            if hasattr(ps_view, "btn_filter") and ps_view.btn_filter.winfo_exists():
                ps_view.btn_filter.configure(text="Применить фильтр" if is_ru else "Apply Filter")
            if hasattr(ps_view, "btn_export") and ps_view.btn_export.winfo_exists():
                ps_view.btn_export.configure(text=self._t("btn_export_sel"))
            if hasattr(ps_view, "btn_copy") and ps_view.btn_copy.winfo_exists():
                ps_view.btn_copy.configure(text="📋 Скопировать имя" if is_ru else "📋 Copy Username")
            if hasattr(ps_view, "btn_open") and ps_view.btn_open.winfo_exists():
                ps_view.btn_open.configure(text="🔗 Открыть на Fragment" if is_ru else "🔗 Open on Fragment")
            if hasattr(ps_view, "tree"):
                col_titles_ps = {
                    "username": self._t("col_username"),
                    "length": self._t("col_length"),
                    "score": self._t("col_score"),
                    "category": self._t("col_category"),
                    "status": self._t("col_status"),
                    "auction": self._t("col_auction"),
                    "checked_at": self._t("col_checked_at"),
                }
                for col, text in col_titles_ps.items():
                    ps_view.tree.heading(col, text=text)

        # Bot Selection View
        bs_view = self.views.get("Bot Selection")
        if bs_view:
            if hasattr(bs_view, "lbl_b") and bs_view.lbl_b.winfo_exists():
                bs_view.lbl_b.configure(text="Свободные боты (Балл >= 70, готовы для BotFather)" if is_ru else "Free Bot Names (Score >= 70, BotFather Ready)")
            if hasattr(bs_view, "lbl_a") and bs_view.lbl_a.winfo_exists():
                bs_view.lbl_a.configure(text="Доступные премиум алиасы (_app, _ai, _game, _agent, _gay)" if is_ru else "Eligible Premium Aliases (_app, _ai, _game, _agent, _gay)")

        # Auction View
        auc_view = self.views.get("Auction Potential")
        if auc_view:
            if hasattr(auc_view, "lbl_title") and auc_view.lbl_title.winfo_exists():
                auc_view.lbl_title.configure(text=self._t("title_auction"))
            if hasattr(auc_view, "lbl_inspect") and auc_view.lbl_inspect.winfo_exists():
                auc_view.lbl_inspect.configure(text=self._t("label_inspect_name"))
            if hasattr(auc_view, "btn_inspect") and auc_view.btn_inspect.winfo_exists():
                auc_view.btn_inspect.configure(text=self._t("btn_inspect"))
            if hasattr(auc_view, "lbl_bench") and auc_view.lbl_bench.winfo_exists():
                auc_view.lbl_bench.configure(text=self._t("lbl_benchmarks"))

        # History View
        hist_view = self.views.get("History")
        if hist_view:
            if hasattr(hist_view, "lbl_title") and hist_view.lbl_title.winfo_exists():
                hist_view.lbl_title.configure(text=self._t("title_history"))
            if hasattr(hist_view, "btn_ref") and hist_view.btn_ref.winfo_exists():
                hist_view.btn_ref.configure(text=self._t("btn_refresh_log"))
            if hasattr(hist_view, "tree"):
                col_titles_hist = {
                    "id": "ID",
                    "type": self._t("col_category"),
                    "username": self._t("col_username"),
                    "status": self._t("col_status"),
                    "source": self._t("col_source"),
                    "time": self._t("col_checked_at"),
                    "details": self._t("col_details"),
                }
                for col, text in col_titles_hist.items():
                    hist_view.tree.heading(col, text=text)

        # Telemetry badge
        self._telemetry_tick(reschedule=False)

    # ================= HUNTER VIEW GENERATOR =================

    def _create_hunter_view(self, hunter_type: str) -> ctk.CTkFrame:
        """Build view for Regular Username Hunter, Bot Hunter, or Premium Bot Names."""
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(3, weight=1)
        view.hunter_type = hunter_type

        # 1. Header & Controls
        header_frame = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        title_key = {
            "REGULAR": "title_regular",
            "BOT": "title_bot",
            "PREMIUM_BOT": "title_premium_bot",
        }[hunter_type]

        lbl_title = ctk.CTkLabel(
            header_frame,
            text=self._t(title_key),
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=TEXT_WHITE,
        )
        lbl_title.pack(anchor="w", padx=16, pady=(12, 6))
        view.lbl_title = lbl_title

        # Control Row
        ctrl_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=16, pady=(0, 12))

        lbl_count = ctk.CTkLabel(ctrl_row, text=self._t("label_generate_count"), font=ctk.CTkFont(weight="bold"))
        lbl_count.pack(side="left", padx=(0, 4))
        view.lbl_count = lbl_count

        count_combo = ctk.CTkComboBox(ctrl_row, values=["100", "250", "500", "1000", "2500", "5000"], width=80)
        count_combo.set("250")
        count_combo.pack(side="left", padx=(0, 8))
        view.count_combo = count_combo

        lbl_mode = ctk.CTkLabel(ctrl_row, text=self._t("label_mode"), font=ctk.CTkFont(weight="bold"))
        lbl_mode.pack(side="left", padx=(0, 4))
        view.lbl_mode = lbl_mode

        mode_values = ["Экономный", "Обычный", "Быстрый"] if self.settings.language == "ru" else ["Economy", "Standard", "Fast"]
        mode_combo = ctk.CTkComboBox(
            ctrl_row,
            values=mode_values,
            width=110,
            command=self._on_mode_selected,
        )
        mode_combo.set(self._mode_to_str(self.settings.performance_mode))
        mode_combo.pack(side="left", padx=(0, 8))
        view.mode_combo = mode_combo

        lbl_workers = ctk.CTkLabel(ctrl_row, text=self._t("label_workers"), font=ctk.CTkFont(weight="bold"))
        lbl_workers.pack(side="left", padx=(0, 4))
        view.lbl_workers = lbl_workers

        concurrency_combo = ctk.CTkComboBox(
            ctrl_row,
            values=["1", "2", "3", "4", "5", "6", "7", "8"],
            width=65,
            command=self._on_concurrency_selected,
        )
        concurrency_combo.set(str(self.settings.get_active_profile().concurrency))
        concurrency_combo.pack(side="left", padx=(0, 10))
        view.concurrency_combo = concurrency_combo

        # Action Buttons
        btn_start = ctk.CTkButton(
            ctrl_row, text=self._t("btn_start"), width=85, fg_color=ACCENT_GREEN, hover_color="#059669",
            command=lambda: self._start_search(hunter_type, int(count_combo.get())),
        )
        btn_start.pack(side="left", padx=3)
        view.btn_start = btn_start

        btn_pause = ctk.CTkButton(
            ctrl_row, text=self._t("btn_pause"), width=75, fg_color=ACCENT_AMBER, hover_color="#d97706",
            command=self.search_service.pause,
        )
        btn_pause.pack(side="left", padx=3)
        view.btn_pause = btn_pause

        btn_resume = ctk.CTkButton(
            ctrl_row, text=self._t("btn_resume"), width=75, fg_color=ACCENT_BLUE, hover_color="#2563eb",
            command=self.search_service.resume,
        )
        btn_resume.pack(side="left", padx=3)
        view.btn_resume = btn_resume

        btn_stop = ctk.CTkButton(
            ctrl_row, text=self._t("btn_stop"), width=75, fg_color=ACCENT_RED, hover_color="#dc2626",
            command=self.search_service.stop,
        )
        btn_stop.pack(side="left", padx=3)
        view.btn_stop = btn_stop

        btn_export = ctk.CTkButton(
            ctrl_row, text=self._t("btn_export"), width=85, fg_color="#7c3aed", hover_color="#6d28d9",
            command=lambda: self._trigger_export(hunter_type),
        )
        btn_export.pack(side="right", padx=3)
        view.btn_export = btn_export

        # 2. Metric Banner
        metric_frame = ctk.CTkFrame(view, fg_color=CARD_DARK, corner_radius=8)
        metric_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=5)
        for c in range(7):
            metric_frame.grid_columnconfigure(c, weight=1)

        prog_label = ctk.CTkLabel(metric_frame, text=f"{self._t('metric_progress')}: 0 / 0", font=ctk.CTkFont(size=12, weight="bold"))
        prog_label.grid(row=0, column=0, padx=6, pady=8)

        speed_label = ctk.CTkLabel(metric_frame, text=f"{self._t('metric_speed')}: 0.0 n/s", font=ctk.CTkFont(size=12))
        speed_label.grid(row=0, column=1, padx=6, pady=8)

        workers_label = ctk.CTkLabel(metric_frame, text=f"{self._t('metric_workers')}: {self.settings.get_active_profile().concurrency}", font=ctk.CTkFont(size=12))
        workers_label.grid(row=0, column=2, padx=6, pady=8)

        avail_label = ctk.CTkLabel(metric_frame, text=f"{self._t('metric_free_found')}: 0", font=ctk.CTkFont(size=12, weight="bold"), text_color="#34d399")
        avail_label.grid(row=0, column=3, padx=6, pady=8)

        err_label = ctk.CTkLabel(metric_frame, text=f"{self._t('metric_errors')}: 0", font=ctk.CTkFont(size=12), text_color="#f87171")
        err_label.grid(row=0, column=4, padx=6, pady=8)

        throttle_label = ctk.CTkLabel(metric_frame, text=self._t("status_normal"), font=ctk.CTkFont(size=12), text_color="#34d399")
        throttle_label.grid(row=0, column=5, padx=6, pady=8)

        status_label = ctk.CTkLabel(metric_frame, text=f"{self._t('metric_status')}: {self._t('status_idle')}", font=ctk.CTkFont(size=12), text_color=TEXT_MUTED)
        status_label.grid(row=0, column=6, padx=6, pady=8)

        # Store widget references on the view object
        view.prog_label = prog_label
        view.speed_label = speed_label
        view.workers_label = workers_label
        view.avail_label = avail_label
        view.err_label = err_label
        view.throttle_label = throttle_label
        view.status_label = status_label

        # 3. Progress Bar
        p_bar = ctk.CTkProgressBar(view, fg_color="#334155", progress_color=ACCENT_BLUE)
        p_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(4, 8))
        p_bar.set(0)
        view.progress_bar = p_bar

        # 4. Results Table (Treeview with dark styling)
        table_frame = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("username", "length", "category", "status", "score", "auction", "checked_at")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        tree.heading("username", text=self._t("col_username"))
        tree.heading("length", text=self._t("col_length"))
        tree.heading("category", text=self._t("col_category"))
        tree.heading("status", text=self._t("col_status"))
        tree.heading("score", text=self._t("col_score"))
        tree.heading("auction", text=self._t("col_auction"))
        tree.heading("checked_at", text=self._t("col_checked_at"))

        tree.column("username", width=180, anchor="w")
        tree.column("length", width=50, anchor="center")
        tree.column("category", width=120, anchor="center")
        tree.column("status", width=180, anchor="center")
        tree.column("score", width=100, anchor="center")
        tree.column("auction", width=180, anchor="center")
        tree.column("checked_at", width=140, anchor="center")

        # Scrollbar
        sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sb.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        view.tree = tree

        # 5. Live Activity Log Box
        log_box = ctk.CTkTextbox(view, height=85, fg_color="#0b1120", text_color="#cbd5e1", font=ctk.CTkFont(family="Consolas", size=11))
        log_box.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 15))
        view.log_box = log_box

        # Attach refresh method
        def refresh_hunter_data():
            tree.delete(*tree.get_children())
            if hunter_type == "REGULAR":
                records = self.db.get_usernames(limit=250)
            elif hunter_type == "BOT":
                records = self.db.get_bots(limit=250)
            else:
                records = self.db.get_premium_aliases(limit=250)

            for r in records:
                tree.insert("", "end", values=(
                    r.username, r.length, r.category, r.status, f"{r.score}/100",
                    r.auction_eligibility, (r.last_checked_at or "")[:19]
                ))
        view.refresh_data = refresh_hunter_data

        return view

    # ================= PREMIUM SELECTION VIEW =================

    def _create_selection_view(self) -> ctk.CTkFrame:
        """Page displaying only confirmed available regular usernames with high score."""
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(2, weight=1)

        # Header
        header = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        lbl = ctk.CTkLabel(header, text=self._t("title_premium_selection"), font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_WHITE)
        lbl.pack(anchor="w", padx=16, pady=(12, 6))
        view.lbl_title = lbl

        # Filter bar
        f_bar = ctk.CTkFrame(header, fg_color="transparent")
        f_bar.pack(fill="x", padx=16, pady=(0, 12))

        lbl_min_score = ctk.CTkLabel(f_bar, text=self._t("label_min_score"), font=ctk.CTkFont(weight="bold"))
        lbl_min_score.pack(side="left", padx=(0, 6))
        view.lbl_min_score = lbl_min_score

        score_combo = ctk.CTkComboBox(f_bar, values=["50+", "60+", "70+", "80+", "90+"], width=80)
        score_combo.set("70+")
        score_combo.pack(side="left", padx=(0, 16))
        view.score_combo = score_combo

        lbl_sort_by = ctk.CTkLabel(f_bar, text=self._t("label_sort_by"), font=ctk.CTkFont(weight="bold"))
        lbl_sort_by.pack(side="left", padx=(0, 6))
        view.lbl_sort_by = lbl_sort_by

        sort_combo = ctk.CTkComboBox(f_bar, values=["Score (High-Low)", "Length (Shortest)", "Date"], width=150)
        sort_combo.set("Score (High-Low)")
        sort_combo.pack(side="left", padx=(0, 16))
        view.sort_combo = sort_combo

        btn_filter = ctk.CTkButton(f_bar, text="Apply Filter", width=100, command=lambda: refresh_sel())
        btn_filter.pack(side="left", padx=4)
        view.btn_filter = btn_filter

        btn_export = ctk.CTkButton(
            f_bar, text=self._t("btn_export_sel"), width=150, fg_color="#7c3aed",
            command=lambda: self._export_premium_sel(int(score_combo.get().replace("+", ""))),
        )
        btn_export.pack(side="right", padx=4)
        view.btn_export = btn_export

        # Action bar: Copy / Open Fragment
        act_bar = ctk.CTkFrame(view, fg_color=CARD_DARK, corner_radius=8)
        act_bar.grid(row=1, column=0, sticky="ew", padx=20, pady=5)

        btn_copy = ctk.CTkButton(act_bar, text="📋 Copy Username", width=130, command=lambda: copy_selected())
        btn_copy.pack(side="left", padx=10, pady=8)
        view.btn_copy = btn_copy

        btn_open = ctk.CTkButton(act_bar, text="🔗 Open on Fragment", width=150, fg_color="#0284c7", command=lambda: open_selected_fragment())
        btn_open.pack(side="left", padx=10, pady=8)
        view.btn_open = btn_open

        sel_count_lbl = ctk.CTkLabel(act_bar, text="Total Matching: 0", font=ctk.CTkFont(size=12, weight="bold"))
        sel_count_lbl.pack(side="right", padx=16, pady=8)
        view.sel_count_lbl = sel_count_lbl

        # Table
        table_frame = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("username", "length", "score", "category", "status", "auction", "checked_at")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        tree.heading("username", text=self._t("col_username"))
        tree.heading("length", text=self._t("col_length"))
        tree.heading("score", text=self._t("col_score"))
        tree.heading("category", text=self._t("col_category"))
        tree.heading("status", text=self._t("col_status"))
        tree.heading("auction", text=self._t("col_auction"))
        tree.heading("checked_at", text=self._t("col_checked_at"))

        tree.column("username", width=180, anchor="w")
        tree.column("length", width=60, anchor="center")
        tree.column("score", width=90, anchor="center")
        tree.column("category", width=130, anchor="center")
        tree.column("status", width=180, anchor="center")
        tree.column("auction", width=180, anchor="center")
        tree.column("checked_at", width=140, anchor="center")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sb.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        view.tree = tree

        def refresh_sel():
            min_sc = int(score_combo.get().replace("+", ""))
            sort_val = sort_combo.get()
            sort_by = "score" if "Score" in sort_val else ("length" if "Length" in sort_val else "date")

            records = self.db.get_usernames(
                limit=1000,
                status=UsernameStatus.AVAILABLE_TO_CLAIM.value,
                min_score=min_sc,
                sort_by=sort_by,
                sort_asc=(sort_by == "length"),
            )
            tree.delete(*tree.get_children())
            for r in records:
                tree.insert("", "end", values=(
                    r.username, r.length, f"{r.score}/100", r.category,
                    r.status, r.auction_eligibility, (r.last_checked_at or "")[:19],
                ))
            is_ru = (self.settings.language == "ru")
            prefix = "Найдено:" if is_ru else "Total Matching:"
            sel_count_lbl.configure(text=f"{prefix} {len(records)}")

        def copy_selected():
            cur = tree.focus()
            if cur:
                val = tree.item(cur, "values")
                if val:
                    self.clipboard_clear()
                    self.clipboard_append(val[0])
                    msg = f"Скопировано @{val[0]} в буфер!" if self.settings.language == "ru" else f"Copied @{val[0]} to clipboard!"
                    messagebox.showinfo("Copied", msg)

        def open_selected_fragment():
            cur = tree.focus()
            if cur:
                val = tree.item(cur, "values")
                if val:
                    webbrowser.open(f"https://fragment.com/username/{val[0]}")

        view.refresh_data = refresh_sel
        return view

    # ================= BOT SELECTION VIEW =================

    def _create_bot_selection_view(self) -> ctk.CTkFrame:
        """Page displaying confirmed available Bot Usernames & Premium Bot Aliases in two tables."""
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=1)

        tabview = ctk.CTkTabview(view, fg_color=PANEL_DARK)
        tabview.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=20, pady=15)
        view.tabview = tabview

        tab_bots = tabview.add("🤖 Standard Bot Names (AVAILABLE_FOR_BOT)")
        tab_aliases = tabview.add("✨ Premium Bot Aliases (ELIGIBLE_FOR_ASSIGNMENT)")

        # Setup Tab 1 (Bots)
        tab_bots.grid_columnconfigure(0, weight=1)
        tab_bots.grid_rowconfigure(1, weight=1)

        top_b = ctk.CTkFrame(tab_bots, fg_color="transparent")
        top_b.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        lbl_b = ctk.CTkLabel(top_b, text="Free Bot Names (Score >= 70, BotFather Ready)", font=ctk.CTkFont(size=15, weight="bold"))
        lbl_b.pack(side="left")
        view.lbl_b = lbl_b

        btn_exp_b = ctk.CTkButton(top_b, text="📥 Export bot_selection.txt", width=160, command=lambda: self.export_service.export_bot_selection(70))
        btn_exp_b.pack(side="right")
        view.btn_exp_b = btn_exp_b

        cols_b = ("username", "length", "score", "category", "status", "auction")
        tree_b = ttk.Treeview(tab_bots, columns=cols_b, show="headings", selectmode="browse")
        for col in cols_b:
            tree_b.heading(col, text=col.capitalize())
            tree_b.column(col, width=130, anchor="center")
        tree_b.column("username", width=180, anchor="w")
        tree_b.grid(row=1, column=0, sticky="nsew")
        view.tree_b = tree_b

        # Setup Tab 2 (Aliases)
        tab_aliases.grid_columnconfigure(0, weight=1)
        tab_aliases.grid_rowconfigure(1, weight=1)

        top_a = ctk.CTkFrame(tab_aliases, fg_color="transparent")
        top_a.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        lbl_a = ctk.CTkLabel(top_a, text="Eligible Premium Aliases (_app, _ai, _game, _agent, _gay)", font=ctk.CTkFont(size=15, weight="bold"))
        lbl_a.pack(side="left")
        view.lbl_a = lbl_a

        btn_exp_a = ctk.CTkButton(top_a, text="📥 Export premium_bot_selection.txt", width=200, command=lambda: self.export_service.export_premium_bot_selection(70))
        btn_exp_a.pack(side="right")
        view.btn_exp_a = btn_exp_a

        cols_a = ("username", "suffix", "length", "score", "category", "status")
        tree_a = ttk.Treeview(tab_aliases, columns=cols_a, show="headings", selectmode="browse")
        for col in cols_a:
            tree_a.heading(col, text=col.capitalize())
            tree_a.column(col, width=130, anchor="center")
        tree_a.column("username", width=180, anchor="w")
        tree_a.grid(row=1, column=0, sticky="nsew")
        view.tree_a = tree_a

        def refresh_both():
            tree_b.delete(*tree_b.get_children())
            bots = self.db.get_bots(limit=500, status=BotStatus.AVAILABLE_FOR_BOT.value, min_score=70)
            for b in bots:
                tree_b.insert("", "end", values=(b.username, b.length, f"{b.score}/100", b.category, b.status, b.auction_eligibility))

            tree_a.delete(*tree_a.get_children())
            aliases = self.db.get_premium_aliases(limit=500, status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value, min_score=70)
            for a in aliases:
                tree_a.insert("", "end", values=(a.username, a.suffix, a.length, f"{a.score}/100", a.category, a.status))

        view.refresh_data = refresh_both
        return view

    # ================= AUCTION POTENTIAL VIEW =================

    def _create_auction_view(self) -> ctk.CTkFrame:
        """Deep dive analysis on Fragment auction eligibility and valuation potential."""
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        lbl = ctk.CTkLabel(header, text=self._t("title_auction"), font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_WHITE)
        lbl.pack(anchor="w", padx=16, pady=(12, 6))
        view.lbl_title = lbl

        # Search box for ad-hoc inspection
        s_box = ctk.CTkFrame(header, fg_color="transparent")
        s_box.pack(fill="x", padx=16, pady=(0, 14))

        lbl_inspect = ctk.CTkLabel(s_box, text=self._t("label_inspect_name"), font=ctk.CTkFont(weight="bold"))
        lbl_inspect.pack(side="left", padx=(0, 8))
        view.lbl_inspect = lbl_inspect

        entry_name = ctk.CTkEntry(s_box, width=220, placeholder_text="e.g. qevrobot or apex")
        entry_name.pack(side="left", padx=(0, 8))
        view.entry_name = entry_name

        btn_inspect = ctk.CTkButton(s_box, text=self._t("btn_inspect"), width=180, command=lambda: inspect_name(entry_name.get()))
        btn_inspect.pack(side="left")
        view.btn_inspect = btn_inspect

        # Results Details Frame
        res_frame = ctk.CTkFrame(view, fg_color=CARD_DARK, corner_radius=10)
        res_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        lbl_tier = ctk.CTkLabel(res_frame, text=f"{self._t('lbl_valuation_tier')} -", font=ctk.CTkFont(size=16, weight="bold"), text_color="#38bdf8")
        lbl_tier.pack(anchor="w", padx=16, pady=(14, 4))
        view.lbl_tier = lbl_tier

        lbl_desc = ctk.CTkLabel(res_frame, text=self._t("msg_inspect_prompt"), font=ctk.CTkFont(size=13), text_color=TEXT_MUTED)
        lbl_desc.pack(anchor="w", padx=16, pady=(0, 8))
        view.lbl_desc = lbl_desc

        lbl_bench = ctk.CTkLabel(res_frame, text=self._t("lbl_benchmarks"), font=ctk.CTkFont(size=13, weight="bold"))
        lbl_bench.pack(anchor="w", padx=16, pady=(4, 2))
        view.lbl_bench = lbl_bench

        bench_box = ctk.CTkTextbox(res_frame, height=100, fg_color="#0f172a", text_color="#e2e8f0", font=ctk.CTkFont(family="Consolas", size=11))
        bench_box.pack(fill="x", padx=16, pady=(0, 14))
        view.bench_box = bench_box

        def inspect_name(raw: str):
            clean = raw.strip().lstrip("@")
            if not clean:
                return
            score, _ = self.search_service.scorer.calculate_score(clean)
            profile = MarketPotentialAnalyzer.get_market_profile(clean, score)

            lbl_tier.configure(text=f"{self._t('lbl_valuation_tier')} {profile['potential_tier']} ({self._t('col_score')}: {score}/100)")
            lbl_desc.configure(text=f"{profile['description']}\n{profile['price_disclaimer']}")

            bench_box.delete("1.0", "end")
            similar = profile.get("similar_benchmarks", [])
            if similar:
                bench_box.insert("end", f"{self._t('lbl_benchmarks')}\n")
                for s in similar:
                    bench_box.insert("end", f" • @{s['name']:<12} sold for {s['price_ton']:,} TON ({s['category']})\n")
            else:
                bench_box.insert("end", self._t("msg_no_similar_bench"))

        return view

    # ================= HISTORY VIEW =================

    def _create_history_view(self) -> ctk.CTkFrame:
        """Audit log of all checks executed."""
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)
        view.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        lbl = ctk.CTkLabel(header, text=self._t("title_history"), font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_WHITE)
        lbl.pack(side="left", padx=16, pady=12)
        view.lbl_title = lbl

        btn_ref = ctk.CTkButton(header, text=self._t("btn_refresh_log"), width=140, command=lambda: refresh_hist())
        btn_ref.pack(side="right", padx=16, pady=12)
        view.btn_ref = btn_ref

        table_frame = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 15))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        cols = ("id", "type", "username", "status", "source", "time", "details")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", selectmode="browse")

        tree.heading("id", text="ID")
        tree.heading("type", text=self._t("col_category"))
        tree.heading("username", text=self._t("col_username"))
        tree.heading("status", text=self._t("col_status"))
        tree.heading("source", text=self._t("col_source"))
        tree.heading("time", text=self._t("col_checked_at"))
        tree.heading("details", text=self._t("col_details"))

        for c in cols:
            tree.column(c, width=120, anchor="center")
        tree.column("username", width=180, anchor="w")
        tree.column("details", width=250, anchor="w")

        sb = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sb.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        view.tree = tree

        def refresh_hist():
            tree.delete(*tree.get_children())
            rows = self.db.get_history(limit=500)
            for r in rows:
                tree.insert("", "end", values=(
                    r["id"], r["target_type"], r["username"], r["new_status"],
                    r["check_source"], r["checked_at"][:19], r["details"],
                ))

        view.refresh_data = refresh_hist
        return view

    # ================= SETTINGS VIEW =================

    def _create_settings_view(self) -> ctk.CTkFrame:
        """Application settings configuration panel."""
        view = ctk.CTkFrame(self.content_container, fg_color="transparent")
        view.grid_columnconfigure(0, weight=1)

        header = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        lbl = ctk.CTkLabel(header, text=self._t("title_settings"), font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_WHITE)
        lbl.pack(anchor="w", padx=16, pady=12)
        view.lbl_title = lbl

        form = ctk.CTkFrame(view, fg_color=PANEL_DARK, corner_radius=10)
        form.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        form.grid_columnconfigure(1, weight=1)

        # Row 0: Language Selection
        lbl_lang = ctk.CTkLabel(form, text=self._t("label_language"), font=ctk.CTkFont(weight="bold"))
        lbl_lang.grid(row=0, column=0, sticky="w", padx=16, pady=8)
        view.lbl_lang = lbl_lang

        lang_combo = ctk.CTkComboBox(
            form,
            values=["Русский (Russian)", "English (Английский)"],
            width=200,
            command=self._on_language_combo_selected,
        )
        lang_combo.set("Русский (Russian)" if self.settings.language == "ru" else "English (Английский)")
        lang_combo.grid(row=0, column=1, sticky="w", padx=16, pady=8)
        view.lang_combo = lang_combo

        # Row 1: Performance Mode
        lbl_mode = ctk.CTkLabel(form, text=self._t("label_perf_mode"), font=ctk.CTkFont(weight="bold"))
        lbl_mode.grid(row=1, column=0, sticky="w", padx=16, pady=8)
        view.lbl_mode = lbl_mode

        mode_values = ["Экономный", "Обычный", "Быстрый"] if self.settings.language == "ru" else ["Economy", "Standard", "Fast"]
        mode_opt = ctk.CTkComboBox(form, values=mode_values, width=140)
        mode_opt.set(self._mode_to_str(self.settings.performance_mode))
        mode_opt.grid(row=1, column=1, sticky="w", padx=16, pady=8)
        view.mode_opt = mode_opt

        # Row 2: Parallel Workers
        lbl_workers = ctk.CTkLabel(form, text=self._t("label_parallel_workers"), font=ctk.CTkFont(weight="bold"))
        lbl_workers.grid(row=2, column=0, sticky="w", padx=16, pady=8)
        view.lbl_workers = lbl_workers

        workers_opt = ctk.CTkComboBox(form, values=["1", "2", "3", "4", "5", "6", "7", "8"], width=90)
        workers_opt.set(str(self.settings.get_active_profile().concurrency))
        workers_opt.grid(row=2, column=1, sticky="w", padx=16, pady=8)
        view.workers_opt = workers_opt

        # Row 3: Delays
        lbl_delay = ctk.CTkLabel(form, text=self._t("label_req_delay"), font=ctk.CTkFont(weight="bold"))
        lbl_delay.grid(row=3, column=0, sticky="w", padx=16, pady=8)
        view.lbl_delay = lbl_delay

        delay_entry = ctk.CTkEntry(form, width=120)
        delay_entry.insert(0, str(self.settings.request_delay_seconds))
        delay_entry.grid(row=3, column=1, sticky="w", padx=16, pady=8)
        view.delay_entry = delay_entry

        # Row 4: Batch Size
        lbl_batch = ctk.CTkLabel(form, text=self._t("label_batch_size"), font=ctk.CTkFont(weight="bold"))
        lbl_batch.grid(row=4, column=0, sticky="w", padx=16, pady=8)
        view.lbl_batch = lbl_batch

        batch_entry = ctk.CTkEntry(form, width=120)
        batch_entry.insert(0, str(self.settings.batch_size))
        batch_entry.grid(row=4, column=1, sticky="w", padx=16, pady=8)
        view.batch_entry = batch_entry

        # Row 5: Min Score Threshold
        lbl_score = ctk.CTkLabel(form, text=self._t("label_min_score_thresh"), font=ctk.CTkFont(weight="bold"))
        lbl_score.grid(row=5, column=0, sticky="w", padx=16, pady=8)
        view.lbl_score = lbl_score

        score_entry = ctk.CTkEntry(form, width=120)
        score_entry.insert(0, str(self.settings.min_score_threshold))
        score_entry.grid(row=5, column=1, sticky="w", padx=16, pady=8)
        view.score_entry = score_entry

        # Row 6: Mock Mode Toggle
        mock_var = ctk.BooleanVar(value=self.settings.mock_mode)
        mock_check = ctk.CTkCheckBox(form, text=self._t("check_mock_mode"), variable=mock_var)
        mock_check.grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=8)
        view.mock_check = mock_check

        # Row 7: Auto Save Toggle
        save_var = ctk.BooleanVar(value=self.settings.auto_save_results)
        save_check = ctk.CTkCheckBox(form, text=self._t("check_auto_save"), variable=save_var)
        save_check.grid(row=7, column=0, columnspan=2, sticky="w", padx=16, pady=8)
        view.save_check = save_check

        # Row 8: Action Buttons
        btn_save = ctk.CTkButton(
            form, text=self._t("btn_save_settings"), width=150, fg_color=ACCENT_GREEN, hover_color="#059669",
            command=lambda: save_conf(),
        )
        btn_save.grid(row=8, column=0, sticky="w", padx=16, pady=(15, 20))
        view.btn_save = btn_save

        btn_clear_db = ctk.CTkButton(
            form, text=self._t("btn_reset_db"), width=150, fg_color=ACCENT_RED, hover_color="#dc2626",
            command=lambda: clear_db(),
        )
        btn_clear_db.grid(row=8, column=1, sticky="w", padx=16, pady=(15, 20))
        view.btn_clear_db = btn_clear_db

        btn_open_exp = ctk.CTkButton(
            form, text=self._t("btn_open_exports"), width=150, fg_color="#475569", hover_color="#334155",
            command=self._open_exports_folder,
        )
        btn_open_exp.grid(row=8, column=2, sticky="w", padx=16, pady=(15, 20))
        view.btn_open_exp = btn_open_exp

        def save_conf():
            try:
                # 1. Language update
                lang_val = lang_combo.get()
                chosen_lang = "ru" if "Рус" in lang_val or "ru" in lang_val.lower() else "en"
                self.settings.language = chosen_lang
                self.db.save_setting("language", chosen_lang)

                # 2. Pipeline parameters
                self.settings.request_delay_seconds = float(delay_entry.get())
                self.settings.batch_size = int(batch_entry.get())
                self.settings.min_score_threshold = int(score_entry.get())
                self.settings.mock_mode = mock_var.get()
                self.settings.auto_save_results = save_var.get()

                # 3. Performance mode and concurrency
                chosen_mode = self._str_to_mode(mode_opt.get())
                chosen_conc = int(workers_opt.get())
                self.search_service.set_performance_mode(chosen_mode, custom_concurrency=chosen_conc)

                # 4. Update checkers
                self.search_service.fragment_checker.mock_mode = self.settings.mock_mode
                self.search_service.telegram_checker.mock_mode = self.settings.mock_mode
                self.search_service.bot_checker.mock_mode = self.settings.mock_mode
                self.search_service.premium_bot_checker.mock_mode = self.settings.mock_mode

                # 5. Apply localized UI strings
                self._apply_language()

                messagebox.showinfo("Saved", self._t("msg_settings_saved"))
            except Exception as e:
                messagebox.showerror(self._t("msg_error"), f"{e}")

        def clear_db():
            if messagebox.askyesno("Confirm", self._t("confirm_reset_db")):
                self.db.clear_all_tables()
                messagebox.showinfo("Cleared", self._t("msg_db_cleared"))

        return view

    # ================= PIPELINE CONTROLS & CALLBACKS =================

    def _start_search(self, hunter_type: str, count: int):
        """Dispatch search execution to the background asyncio thread."""
        if self.search_service.is_running:
            messagebox.showwarning(self._t("msg_error"), self._t("msg_busy"))
            return

        self._active_hunter_type = hunter_type
        current_view_name = {
            "REGULAR": "Username Hunter",
            "BOT": "Bot Username Hunter",
            "PREMIUM_BOT": "Premium Bot Names",
        }[hunter_type]

        view = self.views[current_view_name]
        status_running = f"{self._t('metric_status')}: {self._t('status_running')}"
        view.status_label.configure(text=status_running, text_color="#34d399")
        view.prog_label.configure(text=f"{self._t('metric_progress')}: 0 / {count}")
        view.avail_label.configure(text=f"{self._t('metric_free_found')}: 0")
        view.err_label.configure(text=f"{self._t('metric_errors')}: 0")
        view.progress_bar.set(0)

        if hunter_type == "REGULAR":
            self.worker.submit(self.search_service.run_regular_hunter(count=count))
        elif hunter_type == "BOT":
            self.worker.submit(self.search_service.run_bot_hunter(count=count))
        else:
            self.worker.submit(self.search_service.run_premium_bot_hunter(count=count))

    def _trigger_export(self, hunter_type: str):
        if hunter_type == "REGULAR":
            self.export_service.export_available_usernames()
            self.export_service.export_premium_selection(self.settings.min_score_threshold)
            self.export_service.export_all_usernames_csv()
        elif hunter_type == "BOT":
            self.export_service.export_available_bot_names()
            self.export_service.export_bot_selection(self.settings.min_score_threshold)
            self.export_service.export_all_bot_names_csv()
        else:
            self.export_service.export_premium_bot_names()
            self.export_service.export_premium_bot_selection(self.settings.min_score_threshold)
            self.export_service.export_premium_aliases_csv()

        messagebox.showinfo("Export Complete", f"{self._t('msg_export_complete')}{self.settings.exports_dir}")

    def _export_premium_sel(self, min_score: int):
        self.export_service.export_premium_selection(min_score)
        self.export_service.export_all_usernames_csv()
        messagebox.showinfo("Exported", f"{self._t('msg_export_complete')}{self.settings.exports_dir / 'premium_selection.txt'}")

    def _open_exports_folder(self):
        """Open exports directory in system file manager."""
        try:
            self.settings.exports_dir.mkdir(parents=True, exist_ok=True)
            if hasattr(os, "startfile"):
                os.startfile(self.settings.exports_dir)
            else:
                webbrowser.open(str(self.settings.exports_dir))
        except Exception as e:
            logger.error(f"Failed to open exports directory: {e}")

    def _on_item_checked_callback(self, item: dict[str, Any]):
        """Schedule UI table update on the main Tkinter thread."""
        self.after(0, self._handle_item_ui_update, item)

    def _handle_item_ui_update(self, item: dict[str, Any]):
        target_type = item.get("target_type", self._active_hunter_type)
        view_map = {
            "REGULAR": "Username Hunter",
            "BOT": "Bot Username Hunter",
            "PREMIUM_BOT": "Premium Bot Names",
        }
        target_view = view_map.get(target_type, "Username Hunter")
        v = self.views.get(target_view)
        if v and hasattr(v, "tree"):
            v.tree.insert("", 0, values=(
                item.get("username", ""),
                item.get("length", len(item.get("username", ""))),
                item.get("category", ""),
                item.get("status", ""),
                f"{item.get('score', 0)}/100",
                item.get("auction_eligibility", ""),
                (item.get("last_checked_at", "") or "")[:19],
            ))

    def _on_mode_selected(self, mode_name: str):
        mode = self._str_to_mode(mode_name)
        self.search_service.set_performance_mode(mode)
        profile = self.settings.get_active_profile()
        for v in self.views.values():
            if hasattr(v, "mode_combo"):
                v.mode_combo.set(self._mode_to_str(mode))
            if hasattr(v, "concurrency_combo"):
                v.concurrency_combo.set(str(profile.concurrency))
        self._telemetry_tick(reschedule=False)

    def _on_concurrency_selected(self, conc_str: str):
        try:
            val = int(conc_str)
            if 1 <= val <= 8:
                self.search_service.set_performance_mode(self.settings.performance_mode, custom_concurrency=val)
                for v in self.views.values():
                    if hasattr(v, "concurrency_combo"):
                        v.concurrency_combo.set(str(val))
                self._telemetry_tick(reschedule=False)
        except ValueError:
            pass

    def _telemetry_tick(self, reschedule: bool = True):
        try:
            metrics = self.search_service.get_metrics()
            mode_name = self._mode_to_str(self.settings.performance_mode)
            workers = metrics["active_workers"]
            target = metrics["target_concurrency"]
            ram = metrics["ram_mb"]
            cpu = metrics["cpu_percent"]
            is_thr = metrics["is_throttled"]
            cd = metrics["cooldown_remaining"]

            workers_unit = "ворк." if self.settings.language == "ru" else "workers"
            if not is_thr:
                thr_status = self._t("status_normal")
                thr_color = "#34d399"
            else:
                thr_status = f"{self._t('status_throttled')} ({cd:.1f}s)"
                thr_color = "#f59e0b"

            if hasattr(self, "telemetry_lbl") and self.telemetry_lbl.winfo_exists():
                self.telemetry_lbl.configure(
                    text=f"⚡ {mode_name} ({workers}/{target} {workers_unit})\nRAM: {ram:.1f} MB | CPU: {cpu:.1f}%\n{thr_status}",
                    text_color=thr_color,
                )

            view_map = {
                "REGULAR": "Username Hunter",
                "BOT": "Bot Username Hunter",
                "PREMIUM_BOT": "Premium Bot Names",
            }
            active_view = view_map.get(self._active_hunter_type, "Username Hunter")
            v = self.views.get(active_view)
            if v and hasattr(v, "workers_label"):
                v.workers_label.configure(text=f"{self._t('metric_workers')}: {workers}")
            if v and hasattr(v, "throttle_label"):
                v.throttle_label.configure(
                    text=thr_status,
                    text_color=thr_color,
                )
        except Exception as e:
            logger.debug(f"Telemetry tick error: {e}")
        finally:
            if reschedule:
                self.after(1000, self._telemetry_tick)

    def _on_progress_callback(self, checked: int, total: int, speed: float, available: int, errors: int):
        self.after(0, self._handle_progress_ui_update, checked, total, speed, available, errors)

    def _handle_progress_ui_update(self, checked: int, total: int, speed: float, available: int, errors: int):
        ratio = checked / total if total > 0 else 0
        view_map = {
            "REGULAR": "Username Hunter",
            "BOT": "Bot Username Hunter",
            "PREMIUM_BOT": "Premium Bot Names",
        }
        active_view = view_map.get(self._active_hunter_type, "Username Hunter")
        v = self.views.get(active_view)
        if v and hasattr(v, "progress_bar"):
            v.progress_bar.set(ratio)
            v.prog_label.configure(text=f"{self._t('metric_progress')}: {checked} / {total}")
            unit_speed = "им/с" if self.settings.language == "ru" else "n/s"
            unit_min = "мин" if self.settings.language == "ru" else "min"
            v.speed_label.configure(text=f"{self._t('metric_speed')}: {speed:.1f} {unit_speed} ({speed * 60:.0f}/{unit_min})")
            if hasattr(v, "workers_label"):
                v.workers_label.configure(text=f"{self._t('metric_workers')}: {self.search_service.active_workers_count}")
            v.avail_label.configure(text=f"{self._t('metric_free_found')}: {available}")
            v.err_label.configure(text=f"{self._t('metric_errors')}: {errors}")
            if checked >= total or not self.search_service.is_running:
                v.status_label.configure(text=f"{self._t('metric_status')}: {self._t('status_finished')}", text_color=TEXT_MUTED)
                dash = self.views.get("Dashboard")
                if dash and hasattr(dash, "refresh_stats"):
                    dash.refresh_stats()

    def _on_log_callback(self, message: str):
        self.after(0, self._handle_log_ui_update, message)

    def _handle_log_ui_update(self, message: str):
        view_map = {
            "REGULAR": "Username Hunter",
            "BOT": "Bot Username Hunter",
            "PREMIUM_BOT": "Premium Bot Names",
        }
        active_view = view_map.get(self._active_hunter_type, "Username Hunter")
        v = self.views.get(active_view)
        if v and hasattr(v, "log_box"):
            v.log_box.insert("end", f"{message}\n")
            v.log_box.see("end")
