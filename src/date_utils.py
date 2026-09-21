from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


IST = ZoneInfo("Asia/Kolkata")


def today_ist() -> date:
    return datetime.now(IST).date()


def target_date(days_ahead: int = 1) -> date:
    # Requirement: work only on the immediately following calendar day in India.
    return today_ist() + timedelta(days=days_ahead)
