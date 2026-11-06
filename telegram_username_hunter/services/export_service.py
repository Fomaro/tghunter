"""
Telegram Username Hunter PRO
Export Service (TXT & CSV)
"""
import logging
from pathlib import Path

import pandas as pd

from telegram_username_hunter.config.settings import (
    EXPORTS_DIR,
    AuctionEligibility,
    BotStatus,
    PremiumBotStatus,
    UsernameStatus,
)
from telegram_username_hunter.database.database import DatabaseManager

logger = logging.getLogger(__name__)


class ExportService:
    """Handles automatic and on-demand file exports to TXT and CSV."""

    def __init__(self, db: DatabaseManager, export_dir: Path | None = None):
        self.db = db
        self.export_dir = export_dir or EXPORTS_DIR
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def _write_lines(self, filename: str, lines: list[str]) -> Path:
        out_path = self.export_dir / filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.writelines(f"{line}\n" for line in lines)
        logger.info(f"Exported {len(lines)} lines to {out_path}")
        return out_path

    # ================= TXT EXPORTS =================

    def export_available_usernames(self) -> Path:
        """Export confirmed available regular usernames."""
        records = self.db.get_usernames(limit=50000, status=UsernameStatus.AVAILABLE_TO_CLAIM.value)
        lines = [r.username for r in records]
        return self._write_lines("available_usernames.txt", lines)

    def export_premium_selection(self, min_score: int = 70) -> Path:
        """Export confirmed available regular usernames with score >= min_score."""
        records = self.db.get_usernames(
            limit=50000,
            status=UsernameStatus.AVAILABLE_TO_CLAIM.value,
            min_score=min_score,
            sort_by="score"
        )
        lines = [f"{r.username} (score: {r.score}, length: {r.length}, cat: {r.category})" for r in records]
        return self._write_lines("premium_selection.txt", lines)

    def export_available_bot_names(self) -> Path:
        """Export confirmed available bot usernames."""
        records = self.db.get_bots(limit=50000, status=BotStatus.AVAILABLE_FOR_BOT.value)
        lines = [r.username for r in records]
        return self._write_lines("available_bot_names.txt", lines)

    def export_bot_selection(self, min_score: int = 70) -> Path:
        """Export confirmed available bot usernames with score >= min_score."""
        records = self.db.get_bots(
            limit=50000,
            status=BotStatus.AVAILABLE_FOR_BOT.value,
            min_score=min_score,
            sort_by="score"
        )
        lines = [f"{r.username} (score: {r.score}, length: {r.length}, cat: {r.category})" for r in records]
        return self._write_lines("bot_selection.txt", lines)

    def export_premium_bot_names(self) -> Path:
        """Export eligible premium bot aliases."""
        records = self.db.get_premium_aliases(limit=50000, status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value)
        lines = [r.username for r in records]
        return self._write_lines("premium_bot_names.txt", lines)

    def export_premium_bot_selection(self, min_score: int = 70) -> Path:
        """Export eligible premium bot aliases with score >= min_score."""
        records = self.db.get_premium_aliases(
            limit=50000,
            status=PremiumBotStatus.ELIGIBLE_FOR_ASSIGNMENT.value,
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

    # ================= CSV EXPORTS =================

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
        # Usernames with AUCTION_ELIGIBLE
        records = self.db.get_usernames(limit=100000)
        eligible = [r.to_dict() for r in records if r.auction_eligibility == AuctionEligibility.AUCTION_ELIGIBLE.value]
        df = pd.DataFrame(eligible)
        out_path = self.export_dir / "auction_eligible.csv"
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        return out_path

    def run_all_auto_exports(self, min_score: int = 70) -> None:
        """Run all auto-export routines."""
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
