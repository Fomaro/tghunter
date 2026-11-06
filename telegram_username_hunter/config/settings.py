"""
Telegram Username Hunter PRO
Configuration and Settings Module
"""
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional

# Base Directories
if getattr(sys, "frozen", False):
    # Running as compiled PyInstaller executable (next to the .exe)
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

EXPORTS_DIR = BASE_DIR / "exports"
LOGS_DIR = BASE_DIR / "logs"
DATA_DIR = BASE_DIR / "data"

for directory in (EXPORTS_DIR, LOGS_DIR, DATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)


class UsernameStatus(str, Enum):
    AVAILABLE_TO_CLAIM = "AVAILABLE_TO_CLAIM"
    TAKEN = "TAKEN"
    COLLECTIBLE = "COLLECTIBLE"
    RESERVED = "RESERVED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class BotStatus(str, Enum):
    AVAILABLE_FOR_BOT = "AVAILABLE_FOR_BOT"
    TAKEN = "TAKEN"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class PremiumBotStatus(str, Enum):
    ELIGIBLE_FOR_ASSIGNMENT = "ELIGIBLE_FOR_ASSIGNMENT"
    ALREADY_ASSIGNED = "ALREADY_ASSIGNED"
    INVALID = "INVALID"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"


class AuctionEligibility(str, Enum):
    AUCTION_ELIGIBLE = "AUCTION_ELIGIBLE"
    AUCTION_NOT_SUPPORTED = "AUCTION_NOT_SUPPORTED"
    AUCTION_UNKNOWN = "AUCTION_UNKNOWN"


class UsernameCategory(str, Enum):
    FIVE_CHAR = "5_chars"
    SIX_CHAR = "6_chars"
    SEVEN_CHAR = "7_chars"
    EIGHT_CHAR = "8_chars"
    NINE_TWELVE_CHAR = "9_12_chars"
    DICTIONARY = "dictionary"
    FINANCE = "finance"
    CRYPTO = "crypto"
    TECH = "tech"
    GAMING = "gaming"
    BRAND = "brand"
    RARE_COMBINATION = "rare_combination"
    AI = "ai"
    APPS = "apps"
    AGENTS = "agents"


class PerformanceMode(str, Enum):
    ECONOMY = "ECONOMY"      # Экономный (мин. ресурсов, 1 воркер)
    STANDARD = "STANDARD"    # Обычный (сбалансированный по умолчанию)
    FAST = "FAST"            # Быстрый (макс. скорость в рамках лимитов)


@dataclass
class PerformanceProfile:
    mode: PerformanceMode
    name_ru: str
    description: str
    concurrency: int
    request_delay_seconds: float
    request_jitter_seconds: float
    batch_size: int
    batch_delay_seconds: float
    queue_prefetch_size: int
    max_memory_mb: float = 200.0


PERFORMANCE_PROFILES: dict[PerformanceMode, PerformanceProfile] = {
    PerformanceMode.ECONOMY: PerformanceProfile(
        mode=PerformanceMode.ECONOMY,
        name_ru="Экономный",
        description="Минимальное потребление CPU и RAM, 1 рабочий поток, увеличенные интервалы.",
        concurrency=1,
        request_delay_seconds=2.2,
        request_jitter_seconds=0.4,
        batch_size=5,
        batch_delay_seconds=3.5,
        queue_prefetch_size=20,
        max_memory_mb=120.0,
    ),
    PerformanceMode.STANDARD: PerformanceProfile(
        mode=PerformanceMode.STANDARD,
        name_ru="Обычный",
        description="Сбалансированный режим (по умолчанию), умеренная параллельность и скорость.",
        concurrency=3,
        request_delay_seconds=1.2,
        request_jitter_seconds=0.3,
        batch_size=15,
        batch_delay_seconds=2.0,
        queue_prefetch_size=100,
        max_memory_mb=200.0,
    ),
    PerformanceMode.FAST: PerformanceProfile(
        mode=PerformanceMode.FAST,
        name_ru="Быстрый",
        description="Максимальная скорость в рамках официальных лимитов с адаптивным снижением нагрузки.",
        concurrency=6,
        request_delay_seconds=0.5,
        request_jitter_seconds=0.15,
        batch_size=30,
        batch_delay_seconds=1.0,
        queue_prefetch_size=500,
        max_memory_mb=350.0,
    ),
}


@dataclass
class AppSettings:
    # Database
    db_path: Path = DATA_DIR / "hunter.db"

    # Language / Localization
    language: str = "ru"

    # Performance Mode
    performance_mode: PerformanceMode = PerformanceMode.STANDARD
    custom_concurrency: Optional[int] = None

    # Generation Limits
    default_generation_count: int = 1000
    min_length: int = 5
    max_length: int = 32
    min_score_threshold: int = 70

    # Rate Limiting & Safety (Overridden dynamically by active PerformanceProfile)
    request_delay_seconds: float = 1.2
    request_jitter_seconds: float = 0.3
    batch_size: int = 15
    batch_delay_seconds: float = 2.0
    timeout_seconds: float = 10.0
    max_retries: int = 3
    backoff_factor: float = 2.0
    flood_wait_padding_seconds: float = 10.0

    # Operational Modes
    mock_mode: bool = False
    auto_save_results: bool = True
    auto_export_high_score: bool = True

    # Paths
    exports_dir: Path = EXPORTS_DIR
    logs_dir: Path = LOGS_DIR

    # Logging
    log_level: str = "INFO"

    def get_active_profile(self) -> PerformanceProfile:
        base_prof = PERFORMANCE_PROFILES.get(self.performance_mode, PERFORMANCE_PROFILES[PerformanceMode.STANDARD])
        if self.custom_concurrency is not None and 1 <= self.custom_concurrency <= 8:
            return PerformanceProfile(
                mode=base_prof.mode,
                name_ru=base_prof.name_ru,
                description=base_prof.description,
                concurrency=self.custom_concurrency,
                request_delay_seconds=base_prof.request_delay_seconds,
                request_jitter_seconds=base_prof.request_jitter_seconds,
                batch_size=base_prof.batch_size,
                batch_delay_seconds=base_prof.batch_delay_seconds,
                queue_prefetch_size=base_prof.queue_prefetch_size,
                max_memory_mb=base_prof.max_memory_mb,
            )
        return base_prof

    def to_dict(self) -> dict[str, Any]:
        return {
            "db_path": str(self.db_path),
            "language": self.language,
            "performance_mode": self.performance_mode.value,
            "custom_concurrency": self.custom_concurrency,
            "default_generation_count": self.default_generation_count,
            "min_length": self.min_length,
            "max_length": self.max_length,
            "min_score_threshold": self.min_score_threshold,
            "request_delay_seconds": self.request_delay_seconds,
            "request_jitter_seconds": self.request_jitter_seconds,
            "batch_size": self.batch_size,
            "batch_delay_seconds": self.batch_delay_seconds,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "backoff_factor": self.backoff_factor,
            "flood_wait_padding_seconds": self.flood_wait_padding_seconds,
            "mock_mode": self.mock_mode,
            "auto_save_results": self.auto_save_results,
            "auto_export_high_score": self.auto_export_high_score,
            "log_level": self.log_level,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppSettings":
        settings = cls()
        for k, v in data.items():
            if hasattr(settings, k):
                if k in ("db_path", "exports_dir", "logs_dir"):
                    setattr(settings, k, Path(v))
                elif k == "language":
                    setattr(settings, k, str(v) if str(v) in ("ru", "en") else "ru")
                elif k == "performance_mode":
                    try:
                        setattr(settings, k, PerformanceMode(v))
                    except ValueError:
                        setattr(settings, k, PerformanceMode.STANDARD)
                elif k == "custom_concurrency":
                    setattr(settings, k, int(v) if v is not None else None)
                else:
                    target_type = type(getattr(settings, k))
                    setattr(settings, k, target_type(v))
        return settings


DEFAULT_SETTINGS = AppSettings()
