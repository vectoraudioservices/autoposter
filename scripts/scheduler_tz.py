from __future__ import annotations
from datetime import datetime, timedelta, timezone

def _load_ny_tz():
    """Try IANA zone (needs tzdata on Windows); fallback to fixed -05:00 if missing."""
    try:
        from zoneinfo import ZoneInfo
        try:
            return ZoneInfo("America/New_York")
        except Exception:
            pass
    except Exception:
        pass
    return timezone(timedelta(hours=-5))  # fallback (no DST)

NY = _load_ny_tz()
UTC = timezone.utc

def now_utc() -> datetime:
    return datetime.now(tz=UTC)

def to_utc(dt_local: datetime) -> datetime:
    if dt_local.tzinfo is None:
        raise ValueError("to_utc expects an aware datetime")
    return dt_local.astimezone(UTC)

def to_local(dt_utc: datetime) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=UTC)
    return dt_utc.astimezone(NY)

def _sanitize_hours(hours_24: list[int] | None, default: list[int]) -> list[int]:
    if not hours_24:
        return default[:]
    return sorted({int(h) for h in hours_24 if isinstance(h, int) and 0 <= int(h) <= 23})

def next_local_slot(hours_24: list[int] | None, start_local: datetime | None=None) -> datetime:
    hours = _sanitize_hours(hours_24, default=[11, 15, 19])
    start_l = (start_local or datetime.now(tz=NY)).astimezone(NY)
    base = start_l.replace(minute=0, second=0, microsecond=0)
    for h in hours:
        cand = base.replace(hour=h)
        if cand > start_l:
            return cand.astimezone(UTC)
    cand = base.replace(hour=hours[0]) + timedelta(days=1)
    return cand.astimezone(UTC)

def next_weekly_slot(weekday_0_mon_6_sun: int, hours_24: list[int] | None) -> datetime:
    hours = _sanitize_hours(hours_24, default=[19])
    h = hours[0]
    now_l = datetime.now(tz=NY)
    days_ahead = (weekday_0_mon_6_sun - now_l.weekday()) % 7
    target_l = now_l.replace(hour=h, minute=0, second=0, microsecond=0) + timedelta(days=days_ahead)
    if target_l <= now_l:
        target_l += timedelta(days=7)
    return target_l.astimezone(UTC)
