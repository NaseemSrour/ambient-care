"""Assembles the TRMNL payload and caches it.

TRMNL polls hourly, but the family may also open a live preview. We keep a tiny
in-memory cache that is invalidated whenever (a) the underlying data changes
(via repository.data_version) or (b) the visual time-state changes (period /
day-night / date). This means polls are answered instantly with no heavy work,
while any edit or period change is reflected within seconds.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import repository as repo
from .config import get_settings
from .renderer import RenderContext, render_document, render_fragment
from .time_context import Period, build_time_context
from .models import TaskPeriod


@dataclass
class _CacheEntry:
    signature: str
    fragment: str


_cache: _CacheEntry | None = None


def _period_to_task_period(period: Period) -> TaskPeriod:
    return {
        Period.MORNING: TaskPeriod.MORNING,
        Period.AFTERNOON: TaskPeriod.AFTERNOON,
        Period.EVENING: TaskPeriod.EVENING,
        Period.NIGHT: TaskPeriod.NIGHT,
    }[period]


def build_render_context() -> RenderContext:
    settings = get_settings()
    ctx_time = build_time_context(settings.timezone)

    # Resolve the family message, applying the 24h expiry + warm fallback.
    latest = repo.latest_message()
    if latest is not None:
        message_text, is_fallback = latest.text, False
    else:
        message_text, is_fallback = settings.default_message, True

    tasks = repo.tasks_for_period(_period_to_task_period(ctx_time.period))
    today = ctx_time.now.strftime("%Y-%m-%d")
    events = repo.events_on(today, limit=2)
    # Seed with date+period so the verse changes ~4x/day (once per period) and
    # stays fixed across hourly polls within a period.
    verse_seed = f"{ctx_time.now:%Y-%m-%d}|{ctx_time.period.value}"
    verse = repo.pick_verse(verse_seed)

    return RenderContext(
        time=ctx_time,
        message_text=message_text,
        message_is_fallback=is_fallback,
        tasks=tasks,
        events=events,
        verse=verse,
    )


def _signature(ctx: RenderContext) -> str:
    return f"{ctx.time.period_key}|v{repo.data_version}"


def get_display_fragment(*, use_cache: bool = True) -> str:
    """Return the TRMNL markup fragment, served from cache when still valid."""
    global _cache
    ctx = build_render_context()
    signature = _signature(ctx)

    if use_cache and _cache is not None and _cache.signature == signature:
        return _cache.fragment

    fragment = render_fragment(ctx)
    _cache = _CacheEntry(signature=signature, fragment=fragment)
    return fragment


def get_preview_document() -> str:
    """Full HTML page for browser preview (not cached — preview is rare)."""
    return render_document(build_render_context())
