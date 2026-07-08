"""Time-of-day reasoning for the memory-care display.

Turns "the current moment" into the human, Arabic-first orientation cues the
elder sees: the day name, the Levantine date, the time period, a warm greeting,
and whether the screen should be in Day or Night (inverted) mode.

Design notes for cognitive care:
  * No clock / no minutes are ever shown — exact times cause "time-blindness"
    panic. We only ever communicate a broad *period* of the day.
  * Night mode doubles as the "Time for Sleep" period, giving one strong,
    unambiguous visual cue that the day has ended (helps with sundowning).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from zoneinfo import ZoneInfo


class Period(str, Enum):
    MORNING = "morning"
    AFTERNOON = "afternoon"
    EVENING = "evening"
    NIGHT = "night"  # "Time for Sleep"


class Mode(str, Enum):
    DAY = "day"
    NIGHT = "night"


# Arabic weekday names, indexed by Python's weekday() where Monday == 0.
_ARABIC_WEEKDAYS = {
    0: "الاثنين",
    1: "الثلاثاء",
    2: "الأربعاء",
    3: "الخميس",
    4: "الجمعة",
    5: "السبت",
    6: "الأحد",
}

# Levantine (Bilad al-Sham) Gregorian month names, as used in Jerusalem.
# These are far more familiar to an elder here than transliterated names.
_LEVANTINE_MONTHS = {
    1: "كانون الثاني",
    2: "شباط",
    3: "آذار",
    4: "نيسان",
    5: "أيّار",
    6: "حزيران",
    7: "تمّوز",
    8: "آب",
    9: "أيلول",
    10: "تشرين الأول",
    11: "تشرين الثاني",
    12: "كانون الأول",
}


@dataclass(frozen=True)
class TimeContext:
    """Everything the renderer needs to know about "now"."""

    now: datetime
    period: Period
    mode: Mode
    weekday_ar: str          # e.g. "الأربعاء"
    date_ar: str             # e.g. "8 تمّوز 2026"
    greeting_ar: str         # e.g. "صباح الخير"
    greeting_emoji: str      # e.g. "☀️"
    is_sleep_time: bool

    @property
    def period_key(self) -> str:
        """Stable signature of the visual state, used for caching."""
        return f"{self.date_ar}|{self.period.value}|{self.mode.value}"


def _period_for_hour(hour: int) -> Period:
    if 6 <= hour <= 11:
        return Period.MORNING
    if 12 <= hour <= 16:
        return Period.AFTERNOON
    if 17 <= hour <= 19:
        return Period.EVENING
    return Period.NIGHT  # 20:00 – 05:59


def _greeting_for_period(period: Period) -> tuple[str, str]:
    return {
        Period.MORNING: ("صباح الخير", "☀️"),
        Period.AFTERNOON: ("نهارك سعيد", "🌤️"),
        Period.EVENING: ("مساء الخير", "🌅"),
        Period.NIGHT: ("وقت النوم", "🌙"),
    }[period]


def build_time_context(tz_name: str, *, now: datetime | None = None) -> TimeContext:
    """Compute the full TimeContext for the given timezone.

    `now` can be injected for deterministic testing; otherwise the real
    current time in `tz_name` is used.
    """
    tz = ZoneInfo(tz_name)
    current = now.astimezone(tz) if now else datetime.now(tz)

    period = _period_for_hour(current.hour)
    mode = Mode.DAY if 6 <= current.hour <= 19 else Mode.NIGHT
    greeting, emoji = _greeting_for_period(period)

    weekday_ar = _ARABIC_WEEKDAYS[current.weekday()]
    date_ar = f"{current.day} {_LEVANTINE_MONTHS[current.month]} {current.year}"

    return TimeContext(
        now=current,
        period=period,
        mode=mode,
        weekday_ar=weekday_ar,
        date_ar=date_ar,
        greeting_ar=greeting,
        greeting_emoji=emoji,
        is_sleep_time=(period is Period.NIGHT),
    )
