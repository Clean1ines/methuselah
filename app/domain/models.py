from dataclasses import dataclass, field, asdict
from datetime import datetime, date
from typing import Union, Dict

@dataclass
class DailyEntry:
    """Strict typed domain representation of a user's daily check-in."""
    telegram_id: int
    sleep: float
    energy: int
    mood: int
    activity: str
    food: str
    screen: float
    alcohol: bool
    entry_date: date = field(default_factory=lambda: datetime.now().date())
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Union[int, float, str, bool, date, datetime]]:
        return asdict(self)

@dataclass
class User:
    """Strict typed domain model for an interacting user."""
    telegram_id: int
    streak_days: int = 0
    days_active: int = 0
    gap_days: int = 0
    last_entry_at: Union[datetime, None] = None
    created_at: datetime = field(default_factory=datetime.now)
