"""
Telegram Username Hunter PRO
Export Service (Markdown .md, TXT & CSV)
Saves results into 7 specialized Markdown reports corresponding to all username status types:
1. 1_available.md (Свободные / AVAILABLE)
2. 2_fragment_purchase.md (Можно купить на Fragment / PURCHASE_AVAILABLE)
3. 3_occupied.md (Занятые / OCCUPIED)
4. 4_restricted.md (Ограниченные / RESTRICTED)
5. 5_invalid.md (Недействительные / INVALID)
6. 6_unknown.md (Не проверено / UNKNOWN)
7. 7_errors.md (Ошибки / ERROR)
+ 8_all_statuses.md (Все статусы / ALL)
"""
import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from telegram_username_hunter.config.i18n import (
    format_availability_status,
    format_fragment_status,
)
from telegram_username_hunter.config.settings import (
    EXPORTS_DIR,
    AuctionEligibility,
    BotStatus,
    PremiumBotStatus,
    UsernameStatus,
)
from telegram_username_hunter.database.database import DatabaseManager
from telegram_username_hunter.database.models import (
    BotRecord,
    PremiumAliasRecord,
    UsernameRecord,
)

logger = logging.getLogger(__name__)


def _generate_markdown_report(
    title: str,
    status_label: str,
    usernames: list[UsernameRecord],
    bots: list[BotRecord] | None = None,
    aliases: list[PremiumAliasRecord] | None = None,
) -> str:
    """Generates structured, clean GitHub-flavored Markdown document."""
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    bots_list = bots or []
    aliases_list = aliases or []
    total_count = len(usernames) + len(bots_list) + len(aliases_list)

    md: list[str] = []
    md.append(f"# {title}\n")
    md.append(
        f"> 📊 **Категория статуса:** `{status_label}`  \n"
        f"> 🔢 **Всего записей:** `{total_count}` (Юзернеймы: {len(usernames)}, Боты: {len(bots_list)}, Премиум алиасы: {len(aliases_list)})  \n"
        f"> 🕒 **Дата экспорта:** `{now_str}`  \n"
        f"> 🛡️ **Экспортер:** `Telegram Username Hunter PRO`\n"
    )
    md.append("---\n")

    # 1. Usernames Table
    md.append("## 👤 Юзернеймы Telegram (Usernames)\n")
    if usernames:
        md.append("| № | Юзернейм | Ссылка Telegram | Fragment | Длина | Балл | Категория | Статус доступности | Статус Fragment | Проверено | Примечания |")
        md.append("|---|---|---|---|---|---|---|---|---|---|---|")
        for idx, u in enumerate(usernames, 1):
            clean = u.username.lstrip("@")
            tg_link = f"[{clean}](https://t.me/{clean})"
            frag_link = f"[Fragment](https://fragment.com/username/{clean})"
            avail_txt = format_availability_status(u.status, "ru")
            frag_txt = format_fragment_status(u.auction_eligibility, "ru")
            checked = (u.last_checked_at or "")[:19]
            notes = (u.notes or "").replace("|", "/").replace("\n", " ").strip()
            md.append(
                f"| {idx} | `@{clean}` | {tg_link} | {frag_link} | {u.length} | "
                f"{u.score}/100 | {u.category} | {avail_txt} | {frag_txt} | {checked} | {notes} |"
            )
    else:
        md.append("*В данной категории юзернеймов не обнаружено.*\n")

    # 2. Bot Usernames Table
    if bots_list:
        md.append("\n---\n")
        md.append("## 🤖 Имена ботов (Bot Usernames)\n")
        md.append("| № | Имя бота | Ссылка Telegram | Длина | Балл | Категория | Статус | Проверено | Примечания |")
        md.append("|---|---|---|---|---|---|---|---|---|")
        for idx, b in enumerate(bots_list, 1):
            clean = b.username.lstrip("@")
            tg_link = f"[{clean}](https://t.me/{clean})"
            avail_txt = format_availability_status(b.status, "ru")
            checked = (b.last_checked_at or "")[:19]
            notes = (b.notes or "").replace("|", "/").replace("\n", " ").strip()
            md.append(
                f"| {idx} | `@{clean}` | {tg_link} | {b.length} | {b.score}/100 | "
                f"{b.category} | {avail_txt} | {checked} | {notes} |"
            )

    # 3. Premium Aliases Table
    if aliases_list:
        md.append("\n---\n")
        md.append("## ⭐ Премиум алиасы ботов (Premium Aliases)\n")
        md.append("| № | Премиум алиас | Ссылка Telegram | Суффикс | Балл | Категория | Статус | Проверено |")
        md.append("|---|---|---|---|---|---|---|---|")
        for idx, a in enumerate(aliases_list, 1):
            clean = a.username.lstrip("@")
            tg_link = f"[{clean}](https://t.me/{clean})"
            avail_txt = format_availability_status(a.status, "ru")
            checked = (a.last_checked_at or "")[:19]
            md.append(
                f"| {idx} | `@{clean}` | {tg_link} | `{a.suffix}` | {a.score}/100 | "
                f"{a.category} | {avail_txt} | {checked} |"
            )

    # 4. Quick-copy block
    all_handles: list[str] = (
        [f"@{u.username.lstrip('@')}" for u in usernames] +
        [f"@{b.username.lstrip('@')}" for b in bots_list] +
        [f"@{a.username.lstrip('@')}" for a in aliases_list]
    )
    if all_handles:
        md.append("\n---\n")
        md.append("## 📋 Список для быстрого копирования\n")
        md.append("```text")
        md.extend(all_handles)
        md.append("```\n")

    return "\n".join(md)


class ExportService:
    """Handles automatic and on-demand file exports to Markdown (.md), TXT, and CSV."""

    def __init__(self, db: DatabaseManager, export_dir: Path | None = None):
        self.db = db
        self.export_dir = export_dir or EXPORTS_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def _write_file(self, filename: str, content: str) -> Path:
        out_path = self.export_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Exported {filename} to {out_path}")
        return out_path

    def _write_lines(self, filename: str, lines: list[str]) -> Path:
        out_path = self.export_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(f"{line}\n" for line in lines)
        logger.info(f"Exported {len(lines)} lines to {out_path}")
        return out_path

    # ================= MARKDOWN (.MD) EXPORTS =================

    def export_markdown_available(self) -> Path:
        """1. Export AVAILABLE usernames (excluding Fragment purchases)."""
        all_avail = self.db.get_usernames(limit=100000, status=UsernameStatus.AVAILABLE.value)
        un_avail = [u for u in all_avail if u.auction_eligibility != AuctionEligibility.PURCHASE_AVAILABLE.value]
        bots = self.db.get_bots(limit=100000, status=BotStatus.AVAILABLE.value)
        aliases = self.db.get_premium_aliases(limit=100000, status=PremiumBotStatus.AVAILABLE.value)

        content = _generate_markdown_report(
            title="🟢 Свободные имена Telegram (AVAILABLE)",
            status_label="AVAILABLE",
            usernames=un_avail,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("available.md", content)
        return self._write_file("1_available.md", content)

    def export_markdown_fragment_purchase(self) -> Path:
        """2. Export handles available for purchase on Fragment."""
        usernames = self.db.get_usernames(limit=100000, auction_eligibility=AuctionEligibility.PURCHASE_AVAILABLE.value)
        bots = [b for b in self.db.get_bots(limit=100000) if b.auction_eligibility == AuctionEligibility.PURCHASE_AVAILABLE.value]
        aliases = [a for a in self.db.get_premium_aliases(limit=100000) if a.auction_eligibility == AuctionEligibility.PURCHASE_AVAILABLE.value]

        content = _generate_markdown_report(
            title="💎 Имена для покупки на Fragment (PURCHASE_AVAILABLE)",
            status_label="PURCHASE_AVAILABLE",
            usernames=usernames,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("fragment_purchase.md", content)
        return self._write_file("2_fragment_purchase.md", content)

    def export_markdown_occupied(self) -> Path:
        """3. Export OCCUPIED usernames."""
        usernames = self.db.get_usernames(limit=100000, status=UsernameStatus.OCCUPIED.value)
        bots = self.db.get_bots(limit=100000, status=BotStatus.OCCUPIED.value)
        aliases = self.db.get_premium_aliases(limit=100000, status=PremiumBotStatus.OCCUPIED.value)

        content = _generate_markdown_report(
            title="🔴 Занятые имена Telegram (OCCUPIED)",
            status_label="OCCUPIED",
            usernames=usernames,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("occupied.md", content)
        return self._write_file("3_occupied.md", content)

    def export_markdown_restricted(self) -> Path:
        """4. Export RESTRICTED names (system policy / reserve)."""
        all_restr = self.db.get_usernames(limit=100000, status=UsernameStatus.RESTRICTED.value)
        un_restr = [u for u in all_restr if u.auction_eligibility != AuctionEligibility.PURCHASE_AVAILABLE.value]
        bots = self.db.get_bots(limit=100000, status=BotStatus.RESTRICTED.value)
        aliases = self.db.get_premium_aliases(limit=100000, status=PremiumBotStatus.RESTRICTED.value)

        content = _generate_markdown_report(
            title="🛡️ Ограниченные системной политикой имена (RESTRICTED)",
            status_label="RESTRICTED",
            usernames=un_restr,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("restricted.md", content)
        return self._write_file("4_restricted.md", content)

    def export_markdown_invalid(self) -> Path:
        """5. Export INVALID handles."""
        usernames = self.db.get_usernames(limit=100000, status=UsernameStatus.INVALID.value)
        bots = self.db.get_bots(limit=100000, status=BotStatus.INVALID.value)
        aliases = self.db.get_premium_aliases(limit=100000, status=PremiumBotStatus.INVALID.value)

        content = _generate_markdown_report(
            title="🚫 Недействительные имена Telegram (INVALID)",
            status_label="INVALID",
            usernames=usernames,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("invalid.md", content)
        return self._write_file("5_invalid.md", content)

    def export_markdown_unknown(self) -> Path:
        """6. Export UNKNOWN handles."""
        usernames = self.db.get_usernames(limit=100000, status=UsernameStatus.UNKNOWN.value)
        bots = self.db.get_bots(limit=100000, status=BotStatus.UNKNOWN.value)
        aliases = self.db.get_premium_aliases(limit=100000, status=PremiumBotStatus.UNKNOWN.value)

        content = _generate_markdown_report(
            title="❓ Не проверенные / требующие уточнения имена (UNKNOWN)",
            status_label="UNKNOWN",
            usernames=usernames,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("unknown.md", content)
        return self._write_file("6_unknown.md", content)

    def export_markdown_errors(self) -> Path:
        """7. Export ERROR handles."""
        usernames = self.db.get_usernames(limit=100000, status=UsernameStatus.ERROR.value)
        bots = self.db.get_bots(limit=100000, status=BotStatus.ERROR.value)
        aliases = self.db.get_premium_aliases(limit=100000, status=PremiumBotStatus.ERROR.value)

        content = _generate_markdown_report(
            title="⚠️ Ошибки при проверке имен (ERROR)",
            status_label="ERROR",
            usernames=usernames,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("errors.md", content)
        return self._write_file("7_errors.md", content)

    def export_markdown_all_statuses(self) -> Path:
        """8. Export ALL statuses registry."""
        usernames = self.db.get_usernames(limit=100000)
        bots = self.db.get_bots(limit=100000)
        aliases = self.db.get_premium_aliases(limit=100000)

        content = _generate_markdown_report(
            title="📑 Полный реестр всех проверенных имен (Все статусы)",
            status_label="ALL_STATUSES",
            usernames=usernames,
            bots=bots,
            aliases=aliases,
        )
        self._write_file("all_statuses.md", content)
        return self._write_file("8_all_statuses.md", content)

    def export_all_markdown_reports(self) -> dict[str, Path]:
        """
        Executes generation of all 7 category Markdown (.md) reports plus full registry.
        Returns dict of {filename: Path}.
        """
        return {
            "1_available.md": self.export_markdown_available(),
            "2_fragment_purchase.md": self.export_markdown_fragment_purchase(),
            "3_occupied.md": self.export_markdown_occupied(),
            "4_restricted.md": self.export_markdown_restricted(),
            "5_invalid.md": self.export_markdown_invalid(),
            "6_unknown.md": self.export_markdown_unknown(),
            "7_errors.md": self.export_markdown_errors(),
            "8_all_statuses.md": self.export_markdown_all_statuses(),
        }

    # ================= TXT EXPORTS (BACKWARD COMPATIBILITY) =================

    def export_available_usernames(self) -> Path:
        """Export confirmed available regular usernames."""
        records = self.db.get_usernames(limit=50000, status=UsernameStatus.AVAILABLE.value)
        lines = [r.username for r in records]
        return self._write_lines("available_usernames.txt", lines)

    def export_premium_selection(self, min_score: int = 70) -> Path:
        """Export confirmed available regular usernames with score >= min_score."""
        records = self.db.get_usernames(
            limit=50000,
            status=UsernameStatus.AVAILABLE.value,
            min_score=min_score,
            sort_by="score"
        )
        lines = [f"{r.username} (score: {r.score}, length: {r.length}, cat: {r.category})" for r in records]
        return self._write_lines("premium_selection.txt", lines)

    def export_available_bot_names(self) -> Path:
        """Export confirmed available bot usernames."""
        records = self.db.get_bots(limit=50000, status=BotStatus.AVAILABLE.value)
        lines = [r.username for r in records]
        return self._write_lines("available_bot_names.txt", lines)

    def export_bot_selection(self, min_score: int = 70) -> Path:
        """Export confirmed available bot usernames with score >= min_score."""
        records = self.db.get_bots(
            limit=50000,
            status=BotStatus.AVAILABLE.value,
            min_score=min_score,
            sort_by="score"
        )
        lines = [f"{r.username} (score: {r.score}, length: {r.length}, cat: {r.category})" for r in records]
        return self._write_lines("bot_selection.txt", lines)

    def export_premium_bot_names(self) -> Path:
        """Export eligible premium bot aliases."""
        records = self.db.get_premium_aliases(limit=50000, status=PremiumBotStatus.AVAILABLE.value)
        lines = [r.username for r in records]
        return self._write_lines("premium_bot_names.txt", lines)

    def export_premium_bot_selection(self, min_score: int = 70) -> Path:
        """Export eligible premium bot aliases with score >= min_score."""
        records = self.db.get_premium_aliases(
            limit=50000,
            status=PremiumBotStatus.AVAILABLE.value,
            min_score=min_score,
            sort_by="score"
        )
        lines = [f"{r.username} (score: {r.score}, length: {r.length}, cat: {r.category})" for r in records]
        return self._write_lines("premium_bot_selection.txt", lines)

    def export_unknown_names(self) -> Path:
        """Export names with UNKNOWN status for future re-checking."""
        un_unknown = [r.username for r in self.db.get_usernames(limit=50000, status=UsernameStatus.UNKNOWN.value)]
        bot_unknown = [r.username for r in self.db.get_bots(limit=50000, status=BotStatus.UNKNOWN.value)]
        alias_unknown = [r.username for r in self.db.get_premium_aliases(limit=50000, status=PremiumBotStatus.UNKNOWN.value)]

        lines = sorted(list(set(un_unknown + bot_unknown + alias_unknown)))
        return self._write_lines("unknown_names.txt", lines)

    # ================= CSV EXPORTS (BACKWARD COMPATIBILITY) =================

    def export_all_usernames_csv(self) -> Path:
        records = self.db.get_usernames(limit=100000)
        df = pd.DataFrame([r.to_dict() for r in records])
        out_path = self.export_dir / "all_usernames.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return out_path

    def export_all_bot_names_csv(self) -> Path:
        records = self.db.get_bots(limit=100000)
        df = pd.DataFrame([r.to_dict() for r in records])
        out_path = self.export_dir / "all_bot_names.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return out_path

    def export_premium_aliases_csv(self) -> Path:
        records = self.db.get_premium_aliases(limit=100000)
        df = pd.DataFrame([r.to_dict() for r in records])
        out_path = self.export_dir / "premium_aliases.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return out_path

    def export_auction_eligible_csv(self) -> Path:
        records = self.db.get_usernames(limit=100000)
        eligible = [
            r.to_dict()
            for r in records
            if r.auction_eligibility in (
                AuctionEligibility.AUCTION_SUPPORTED.value,
                AuctionEligibility.PURCHASE_AVAILABLE.value,
            )
        ]
        df = pd.DataFrame(eligible)
        out_path = self.export_dir / "auction_eligible.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return out_path

    def run_all_auto_exports(self, min_score: int = 70) -> None:
        """Run all auto-export routines including Markdown reports."""
        self.export_all_markdown_reports()
        self.export_available_usernames()
        self.export_premium_selection(min_score)
        self.export_available_bot_names()
        self.export_bot_selection(min_score)
        self.export_premium_bot_names()
        self.export_premium_bot_selection(min_score)
        self.export_unknown_names()
        self.export_all_usernames_csv()
        self.export_all_bot_names_csv()
        self.export_premium_aliases_csv()
        self.export_auction_eligible_csv()
