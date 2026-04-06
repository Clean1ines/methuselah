from typing import Dict, Union
from datetime import date, datetime
from app.domain.models import User, DailyEntry

class ContextBuilder:
    """Builds unified, flat property-graph dictionary to be fed to DSL engine."""
    @staticmethod
    def build(user: User, entry: DailyEntry) -> Dict[str, Union[str, int, float, bool, date, datetime]]:
        """Extracts strictly valid context map preventing duplicate definitions upstream."""
        return {
            **entry.to_dict(),
            "streak_days": user.streak_days,
            "days_active": user.days_active,
            "gap_days": user.gap_days,
        }
