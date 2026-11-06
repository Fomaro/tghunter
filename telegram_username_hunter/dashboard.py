"""
Telegram Username Hunter PRO
Dashboard View Component
"""
from collections.abc import Callable

import customtkinter as ctk

from telegram_username_hunter.database.database import DatabaseManager


class StatCard(ctk.CTkFrame):
    """Reusable metric card for the dashboard."""

    def __init__(
        self,
        master,
        title: str,
        value: str,
        accent_color: str = "#3a82f6",
        icon_text: str = "📊",
        **kwargs
    ):
        super().__init__(master, fg_color="#1e222d", corner_radius=10, **kwargs)

        self.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(14, 4))

        self.icon_label = ctk.CTkLabel(
            header_frame,
            text=icon_text,
            font=ctk.CTkFont(size=20),
            text_color=accent_color
        )
        self.icon_label.pack(side="left")

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8"
        )
        self.title_label.pack(side="left", padx=8)

        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#f8fafc"
        )
        self.value_label.pack(anchor="w", padx=16, pady=(2, 14))

    def update_value(self, new_val: str) -> None:
        self.value_label.configure(text=new_val)


class DashboardView(ctk.CTkFrame):
    """Main dashboard displaying aggregated system metrics and recent events."""

    def __init__(self, master, db: DatabaseManager, on_navigate: Callable[[str], None] | None = None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.db = db
        self.on_navigate = on_navigate

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header Title
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        self.title_lbl = ctk.CTkLabel(
            title_frame,
            text="🚀 Dashboard & System Overview",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#f1f5f9"
        )
        self.title_lbl.pack(side="left")

        self.refresh_btn = ctk.CTkButton(
            title_frame,
            text="🔄 Refresh Stats",
            width=120,
            height=32,
            fg_color="#334155",
            hover_color="#475569",
            command=self.refresh_stats
        )
        self.refresh_btn.pack(side="right")

        # Stat Cards Grid (4 columns x 2 rows)
        cards_grid = ctk.CTkFrame(self, fg_color="transparent")
        cards_grid.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        for col in range(4):
            cards_grid.grid_columnconfigure(col, weight=1, uniform="stat_cards")

        self.card_generated = StatCard(cards_grid, "Total Generated", "0", "#38bdf8", "⚡")
        self.card_generated.grid(row=0, column=0, padx=6, pady=6, sticky="ew")

        self.card_checked = StatCard(cards_grid, "Total Checked", "0", "#818cf8", "🔍")
        self.card_checked.grid(row=0, column=1, padx=6, pady=6, sticky="ew")

        self.card_free_un = StatCard(cards_grid, "Free Usernames", "0", "#34d399", "🟢")
        self.card_free_un.grid(row=0, column=2, padx=6, pady=6, sticky="ew")

        self.card_free_bot = StatCard(cards_grid, "Free Bot Names", "0", "#10b981", "🤖")
        self.card_free_bot.grid(row=0, column=3, padx=6, pady=6, sticky="ew")

        self.card_premium_alias = StatCard(cards_grid, "Premium Bot Aliases", "0", "#fbbf24", "✨")
        self.card_premium_alias.grid(row=1, column=0, padx=6, pady=6, sticky="ew")

        self.card_promising_un = StatCard(cards_grid, "Promising Usernames (70+)", "0", "#f43f5e", "💎")
        self.card_promising_un.grid(row=1, column=1, padx=6, pady=6, sticky="ew")

        self.card_promising_bot = StatCard(cards_grid, "Promising Bots (70+)", "0", "#ec4899", "🔥")
        self.card_promising_bot.grid(row=1, column=2, padx=6, pady=6, sticky="ew")

        self.card_errors = StatCard(cards_grid, "Verification Errors", "0", "#ef4444", "⚠️")
        self.card_errors.grid(row=1, column=3, padx=6, pady=6, sticky="ew")

        # Bottom Frame: Recent Activity & Quick Navigation
        bottom_frame = ctk.CTkFrame(self, fg_color="#1e222d", corner_radius=10)
        bottom_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 20))
        bottom_frame.grid_columnconfigure(0, weight=3)
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_rowconfigure(1, weight=1)

        # Activity Title
        self.act_header = ctk.CTkLabel(
            bottom_frame,
            text="🕒 Recent Activity Log",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc"
        )
        self.act_header.grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        self.quick_header = ctk.CTkLabel(
            bottom_frame,
            text="⚡ Quick Actions",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f8fafc"
        )
        self.quick_header.grid(row=0, column=1, sticky="w", padx=16, pady=(14, 8))

        # Recent Activity Textbox
        self.activity_box = ctk.CTkTextbox(
            bottom_frame,
            fg_color="#0f172a",
            text_color="#94a3b8",
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8
        )
        self.activity_box.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Quick Actions Panel
        actions_panel = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        actions_panel.grid(row=1, column=1, sticky="nsew", padx=16, pady=(0, 16))

        self.btn_hunt_un = ctk.CTkButton(
            actions_panel,
            text="🎯 Hunt Usernames",
            height=38,
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            command=lambda: self.on_navigate("Username Hunter") if self.on_navigate else None
        )
        self.btn_hunt_un.pack(fill="x", pady=6)

        self.btn_hunt_bot = ctk.CTkButton(
            actions_panel,
            text="🤖 Hunt Bot Names",
            height=38,
            fg_color="#059669",
            hover_color="#047857",
            command=lambda: self.on_navigate("Bot Username Hunter") if self.on_navigate else None
        )
        self.btn_hunt_bot.pack(fill="x", pady=6)

        self.btn_hunt_alias = ctk.CTkButton(
            actions_panel,
            text="✨ Hunt Premium Aliases",
            height=38,
            fg_color="#d97706",
            hover_color="#b45309",
            command=lambda: self.on_navigate("Premium Bot Names") if self.on_navigate else None
        )
        self.btn_hunt_alias.pack(fill="x", pady=6)

        self.btn_view_selection = ctk.CTkButton(
            actions_panel,
            text="💎 View Premium Selection",
            height=38,
            fg_color="#7c3aed",
            hover_color="#6d28d9",
            command=lambda: self.on_navigate("Premium Selection") if self.on_navigate else None
        )
        self.btn_view_selection.pack(fill="x", pady=6)

        self._current_lang = "ru"
        self.apply_language("ru")
        self.refresh_stats()

    def apply_language(self, lang: str = "ru") -> None:
        """Dynamically update dashboard text and card titles based on language."""
        self._current_lang = lang
        is_ru = (lang == "ru")

        self.title_lbl.configure(text="🚀 Панель управления и обзор системы" if is_ru else "🚀 Dashboard & System Overview")
        self.refresh_btn.configure(text="🔄 Обновить статистику" if is_ru else "🔄 Refresh Stats")

        self.card_generated.title_label.configure(text="Всего сгенерировано" if is_ru else "Total Generated")
        self.card_checked.title_label.configure(text="Всего проверено" if is_ru else "Total Checked")
        self.card_free_un.title_label.configure(text="Свободные username" if is_ru else "Free Usernames")
        self.card_free_bot.title_label.configure(text="Свободные боты" if is_ru else "Free Bot Names")
        self.card_premium_alias.title_label.configure(text="Премиум алиасы" if is_ru else "Premium Bot Aliases")
        self.card_promising_un.title_label.configure(text="Перспективные (70+)" if is_ru else "Promising Names (70+)")
        self.card_promising_bot.title_label.configure(text="Перспективные боты (70+)" if is_ru else "Promising Bots (70+)")
        self.card_errors.title_label.configure(text="Ошибки проверки" if is_ru else "Verification Errors")

        self.act_header.configure(text="🕒 Журнал активности" if is_ru else "🕒 Recent Activity Log")
        self.quick_header.configure(text="⚡ Быстрые действия" if is_ru else "⚡ Quick Actions")

        self.btn_hunt_un.configure(text="🎯 Поиск юзернеймов" if is_ru else "🎯 Hunt Usernames")
        self.btn_hunt_bot.configure(text="🤖 Поиск ботов" if is_ru else "🤖 Hunt Bot Names")
        self.btn_hunt_alias.configure(text="✨ Премиум имена ботов" if is_ru else "✨ Hunt Premium Aliases")
        self.btn_view_selection.configure(text="💎 Премиум отбор" if is_ru else "💎 View Premium Selection")

    def refresh_stats(self) -> None:
        """Fetch latest figures from DB and update card values."""
        stats = self.db.get_dashboard_stats()
        self.card_generated.update_value(f"{stats.total_generated:,}")
        self.card_checked.update_value(f"{stats.total_checked:,}")
        self.card_free_un.update_value(f"{stats.available_usernames:,}")
        self.card_free_bot.update_value(f"{stats.available_bot_names:,}")
        self.card_premium_alias.update_value(f"{stats.premium_bot_aliases:,}")
        self.card_promising_un.update_value(f"{stats.promising_usernames:,}")
        self.card_promising_bot.update_value(f"{stats.promising_bot_names:,}")
        self.card_errors.update_value(f"{stats.check_errors:,}")

        # Update activity log
        history = self.db.get_history(limit=25)
        self.activity_box.delete("1.0", "end")
        if not history:
            self.activity_box.insert("end", "No check activity recorded yet.\nClick 'Hunt Usernames' to begin searching!")
        else:
            for item in history:
                timestamp = item.get("checked_at", "")[:19]
                target = item.get("username", "")
                status = item.get("new_status", "")
                source = item.get("check_source", "")
                line = f"[{timestamp}] @{target:<20} | Status: {status:<24} | Source: {source}\n"
                self.activity_box.insert("end", line)
