"""
Telegram Username Hunter PRO
Internationalization and Localization (i18n) Module
Supports Russian (ru) and English (en) interfaces with dynamic switching.
"""

TRANSLATIONS: dict[str, dict[str, str]] = {
    "ru": {
        # App brand & window
        "app_title": "Telegram Username Hunter PRO v2.5",
        "brand_title": "⚡ TG Hunter PRO",
        "brand_subtitle": "Разведка имён Telegram и Fragment",

        # Navigation
        "nav_dashboard": "Панель управления",
        "nav_username_hunter": "Поиск юзернеймов",
        "nav_bot_hunter": "Поиск ботов",
        "nav_premium_bot": "Премиум имена ботов",
        "nav_premium_selection": "Премиум отбор",
        "nav_bot_selection": "Отбор ботов",
        "nav_auction_potential": "Аукционный потенциал",
        "nav_history": "История проверок",
        "nav_settings": "Настройки",

        # Mode and status badges
        "badge_safe_rate_limits": "🟢 Безопасные лимиты",
        "badge_mock_mode": "🧪 Тестовый Mock-режим",
        "status_normal": "🟢 Обычный",
        "status_throttled": "⚠️ Замедление",
        "status_cooldown": "⚠️ Ожидание",
        "status_idle": "ОЖИДАНИЕ",
        "status_running": "В РАБОТЕ",
        "status_finished": "ЗАВЕРШЕНО",

        # Performance modes
        "mode_economy": "Экономный",
        "mode_standard": "Обычный",
        "mode_fast": "Быстрый",

        # Hunter Views Header & Controls
        "title_regular": "🎯 Поиск Telegram юзернеймов",
        "title_bot": "🤖 Поиск юзернеймов ботов",
        "title_premium_bot": "✨ Премиум имена и алиасы ботов",
        "label_generate_count": "Количество:",
        "label_mode": "Режим:",
        "label_workers": "Потоки:",
        "btn_start": "▶ Старт",
        "btn_pause": "⏸ Пауза",
        "btn_resume": "⏯ Продолжить",
        "btn_stop": "⏹ Стоп",
        "btn_export": "📥 Экспорт",

        # Metrics Banner
        "metric_progress": "Прогресс",
        "metric_speed": "Скорость",
        "metric_workers": "Воркеры",
        "metric_free_found": "🟢 Свободно",
        "metric_errors": "⚠️ Ошибки",
        "metric_status": "Статус",

        # Table Column Headers
        "col_username": "Username",
        "col_length": "Длина",
        "col_category": "Категория",
        "col_status": "Статус проверки",
        "col_score": "Оценка (0-100)",
        "col_auction": "Допуск к Fragment",
        "col_checked_at": "Время проверки",
        "col_details": "Детали",
        "col_source": "Источник",

        # Premium Selection View
        "title_premium_selection": "💎 Премиум отбор (Свободные имена с высоким баллом)",
        "label_min_score": "Мин. балл:",
        "label_sort_by": "Сортировка:",
        "btn_export_sel": "📥 Экспорт отбора",

        # Bot Selection View
        "title_bot_selection": "⭐ Отбор свободных имён ботов",

        # Auction View
        "title_auction": "🏷️ Аналитика аукционного потенциала Fragment",
        "label_inspect_name": "Проверить имя:",
        "placeholder_inspect": "например, qevrobot или apex",
        "btn_inspect": "🔍 Рассчитать рыночный потенциал",
        "lbl_valuation_tier": "Категория оценки:",
        "lbl_benchmarks": "Исторические ориентиры продаж на Fragment:",
        "msg_inspect_prompt": "Введите имя выше для расчёта факторов скоринга и проверки на Fragment.",
        "msg_no_similar_bench": "Прямых совпадений в истории не найдено. Анализ выполнен алгоритмически.",

        # History View
        "title_history": "📜 История проверок и журнал аудита",
        "btn_refresh_log": "🔄 Обновить журнал",

        # Settings View
        "title_settings": "⚙️ Настройки и параметры приложения",
        "label_language": "Язык интерфейса:",
        "lang_ru": "Русский (Russian)",
        "lang_en": "English (Английский)",
        "label_perf_mode": "Режим производительности:",
        "label_parallel_workers": "Параллельные воркеры (1-8):",
        "label_req_delay": "Задержка запросов (секунды):",
        "label_batch_size": "Размер пакета:",
        "label_min_score_thresh": "Мин. балл для отбора (0-100):",
        "check_mock_mode": "Тестовый офлайн-режим (Mock Mode без сетевых вызовов)",
        "check_auto_save": "Автоматически сохранять и экспортировать перспективные имена",
        "btn_save_settings": "💾 Сохранить настройки",
        "btn_reset_db": "🗑️ Очистить базу данных",
        "btn_open_exports": "📂 Папка экспорта",
        "confirm_reset_db": "Вы уверены, что хотите удалить все сохранённые имена и историю?",
        "msg_db_cleared": "База данных успешно очищена.",
        "msg_settings_saved": "Настройки успешно применены!",
        "msg_error": "Ошибка",
        "msg_busy": "Поисковый пайплайн уже активно выполняется!",
        "msg_export_complete": "Файлы успешно экспортированы в:\n",

        # Dashboard View
        "dash_title": "📊 Панель управления и статистика",
        "dash_total_generated": "Всего сгенерировано",
        "dash_total_checked": "Всего проверено",
        "dash_free_usernames": "Свободные username",
        "dash_free_bots": "Свободные боты",
        "dash_premium_aliases": "Премиум алиасы",
        "dash_promising_un": "Перспективные имена",
        "dash_promising_bots": "Перспективные боты",
        "dash_errors": "Ошибки проверки",
        "dash_last_activity": "Последняя активность",
        "dash_btn_regular": "🎯 Поиск юзернеймов",
        "dash_btn_bot": "🤖 Поиск ботов",
        "dash_btn_premium": "✨ Премиум имена ботов",
    },
    "en": {
        # App brand & window
        "app_title": "Telegram Username Hunter PRO v2.5",
        "brand_title": "⚡ TG Hunter PRO",
        "brand_subtitle": "Fragment & Username Intelligence",

        # Navigation
        "nav_dashboard": "Dashboard",
        "nav_username_hunter": "Username Hunter",
        "nav_bot_hunter": "Bot Username Hunter",
        "nav_premium_bot": "Premium Bot Names",
        "nav_premium_selection": "Premium Selection",
        "nav_bot_selection": "Bot Selection",
        "nav_auction_potential": "Auction Potential",
        "nav_history": "History",
        "nav_settings": "Settings",

        # Mode and status badges
        "badge_safe_rate_limits": "🟢 Safe Rate Limits",
        "badge_mock_mode": "🧪 Mock Offline Mode",
        "status_normal": "🟢 Normal",
        "status_throttled": "⚠️ Throttled",
        "status_cooldown": "⚠️ Cooldown",
        "status_idle": "IDLE",
        "status_running": "RUNNING",
        "status_finished": "FINISHED",

        # Performance modes
        "mode_economy": "Economy",
        "mode_standard": "Standard",
        "mode_fast": "Fast",

        # Hunter Views Header & Controls
        "title_regular": "🎯 Telegram Username Hunter",
        "title_bot": "🤖 Bot Username Hunter",
        "title_premium_bot": "✨ Premium Bot Names & Aliases",
        "label_generate_count": "Count:",
        "label_mode": "Mode:",
        "label_workers": "Workers:",
        "btn_start": "▶ Start",
        "btn_pause": "⏸ Pause",
        "btn_resume": "⏯ Resume",
        "btn_stop": "⏹ Stop",
        "btn_export": "📥 Export",

        # Metrics Banner
        "metric_progress": "Progress",
        "metric_speed": "Speed",
        "metric_workers": "Workers",
        "metric_free_found": "🟢 Free Found",
        "metric_errors": "⚠️ Errors",
        "metric_status": "Status",

        # Table Column Headers
        "col_username": "Username",
        "col_length": "Length",
        "col_category": "Category",
        "col_status": "Verification Status",
        "col_score": "Score (0-100)",
        "col_auction": "Auction Eligibility",
        "col_checked_at": "Checked At",
        "col_details": "Details",
        "col_source": "Source",

        # Premium Selection View
        "title_premium_selection": "💎 Premium Selection (Confirmed Free Usernames)",
        "label_min_score": "Min Score:",
        "label_sort_by": "Sort By:",
        "btn_export_sel": "📥 Export Selection",

        # Bot Selection View
        "title_bot_selection": "⭐ Bot Selection (Confirmed Free Bot Names)",

        # Auction View
        "title_auction": "🏷️ Fragment Auction Potential & Market Intelligence",
        "label_inspect_name": "Inspect Username:",
        "placeholder_inspect": "e.g. qevrobot or apex",
        "btn_inspect": "🔍 Analyze Market Potential",
        "lbl_valuation_tier": "Valuation Tier:",
        "lbl_benchmarks": "Historical Fragment Sales Benchmarks:",
        "msg_inspect_prompt": "Enter a username above to calculate scoring breakdown and Fragment eligibility.",
        "msg_no_similar_bench": "No direct historical sales match. Linguistic structure analyzed algorithmically.",

        # History View
        "title_history": "📜 Verification History & Audit Log",
        "btn_refresh_log": "🔄 Refresh Log",

        # Settings View
        "title_settings": "⚙️ Settings & Pipeline Configuration",
        "label_language": "Interface Language:",
        "lang_ru": "Русский (Russian)",
        "lang_en": "English (Английский)",
        "label_perf_mode": "Performance Mode:",
        "label_parallel_workers": "Parallel Workers (1-8):",
        "label_req_delay": "Request Delay (seconds):",
        "label_batch_size": "Batch Size:",
        "label_min_score_thresh": "Min Score for Selection (0-100):",
        "check_mock_mode": "Enable Mock / Offline Mode (Fast testing without network calls)",
        "check_auto_save": "Automatically save & export high-score names upon completion",
        "btn_save_settings": "💾 Save Settings",
        "btn_reset_db": "🗑️ Reset Database",
        "btn_open_exports": "📂 Open Exports",
        "confirm_reset_db": "Are you sure you want to clear all stored names and history?",
        "msg_db_cleared": "Database reset complete.",
        "msg_settings_saved": "Settings applied successfully!",
        "msg_error": "Error",
        "msg_busy": "A search pipeline is already actively running!",
        "msg_export_complete": "Export files saved to:\n",

        # Dashboard View
        "dash_title": "📊 Dashboard & Statistics",
        "dash_total_generated": "Total Generated",
        "dash_total_checked": "Total Checked",
        "dash_free_usernames": "Free Usernames",
        "dash_free_bots": "Free Bots",
        "dash_premium_aliases": "Premium Aliases",
        "dash_promising_un": "Promising Names",
        "dash_promising_bots": "Promising Bots",
        "dash_errors": "Check Errors",
        "dash_last_activity": "Last Activity",
        "dash_btn_regular": "🎯 Launch Username Hunter",
        "dash_btn_bot": "🤖 Launch Bot Hunter",
        "dash_btn_premium": "✨ Launch Premium Bot Names",
    }
}


def tr(key: str, lang: str = "ru", default: str | None = None) -> str:
    """Retrieve localized string by key and language code."""
    lang_map = TRANSLATIONS.get(lang, TRANSLATIONS["ru"])
    if key in lang_map:
        return lang_map[key]
    # Fallback to English if not in Russian
    en_map = TRANSLATIONS.get("en", {})
    if key in en_map:
        return en_map[key]
    return default if default is not None else key
