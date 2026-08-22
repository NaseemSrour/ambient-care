"""Generates the 800x480 monochrome markup shown on the TRMNL e-paper screen.

Two outputs from the same logic:
  * render_fragment() -> a SELF-CONTAINED fragment (scoped <style> + one root
    <div>). This is what we hand to TRMNL: its private-plugin editor injects
    your markup inside its own page via Liquid `{{ html }}`, so a nested full
    <html> document would render unreliably. Everything here is scoped under
    `.ac-root` and the Cairo font is pulled in with @import.
  * render_document() -> the fragment wrapped in a full HTML page, purely for
    browser previews (/api/trmnl.html).

Design rules (see Memory-loss Care Features):
  * Everything is Arabic, right-to-left, Cairo font, large and legible.
  * Only pure black and white — no greys that dither badly on e-ink.
  * Day mode = white background / black text; Night mode = inverted, acting as
    a strong "the day has ended" cue.
  * Deliberately minimal: the day-time greeting fills the top ~80% of the panel
    as one huge, unmissable orientation cue, and a single warm family message
    sits in the bottom ~20%. No clock, no minutes, no lists, no clutter.
"""
from __future__ import annotations

import html
from dataclasses import dataclass

from .config import get_settings
from .time_context import Mode, Period, TimeContext


# Period icons drawn as SVG shapes (not font emoji) so they render as crisp,
# reliable black/white on the 1-bit e-ink panel. They use currentColor, so they
# follow the greeting color: black in day mode, white at night.
_PERIOD_ICONS: dict[Period, str] = {
    # Morning — full sun with rays
    Period.MORNING: (
        '<svg class="pic" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="32" cy="32" r="12" fill="currentColor"/>'
        '<g stroke="currentColor" stroke-width="5" stroke-linecap="round">'
        '<line x1="32" y1="3" x2="32" y2="12"/><line x1="32" y1="52" x2="32" y2="61"/>'
        '<line x1="3" y1="32" x2="12" y2="32"/><line x1="52" y1="32" x2="61" y2="32"/>'
        '<line x1="11" y1="11" x2="17" y2="17"/><line x1="47" y1="47" x2="53" y2="53"/>'
        '<line x1="53" y1="11" x2="47" y2="17"/><line x1="17" y1="47" x2="11" y2="53"/>'
        "</g></svg>"
    ),
    # Afternoon — sun peeking behind a cloud
    Period.AFTERNOON: (
        '<svg class="pic" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        '<circle cx="24" cy="22" r="10" fill="currentColor"/>'
        '<g stroke="currentColor" stroke-width="4" stroke-linecap="round">'
        '<line x1="24" y1="4" x2="24" y2="10"/><line x1="6" y1="22" x2="12" y2="22"/>'
        '<line x1="10" y1="8" x2="14" y2="12"/><line x1="38" y1="8" x2="34" y2="12"/></g>'
        '<g fill="currentColor"><circle cx="28" cy="44" r="10"/>'
        '<circle cx="41" cy="45" r="12"/><circle cx="51" cy="47" r="8"/>'
        '<rect x="26" y="46" width="29" height="12" rx="6"/></g></svg>'
    ),
    # Evening — sun setting over the horizon
    Period.EVENING: (
        '<svg class="pic" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M20 42 a12 12 0 0 1 24 0 Z" fill="currentColor"/>'
        '<g stroke="currentColor" stroke-width="5" stroke-linecap="round">'
        '<line x1="32" y1="12" x2="32" y2="20"/><line x1="12" y1="28" x2="17" y2="31"/>'
        '<line x1="52" y1="28" x2="47" y2="31"/><line x1="6" y1="42" x2="18" y2="42"/>'
        '<line x1="46" y1="42" x2="58" y2="42"/><line x1="12" y1="54" x2="52" y2="54"/>'
        "</g></svg>"
    ),
    # Night — crescent moon with a sparkle
    Period.NIGHT: (
        '<svg class="pic" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">'
        '<path d="M48 34 A17 17 0 1 1 30 17 A13 13 0 1 0 48 34 Z" fill="currentColor"/>'
        '<path d="M52 7 l1.8 5.6 l5.6 1.8 l-5.6 1.8 l-1.8 5.6 l-1.8-5.6 l-5.6-1.8 l5.6-1.8 Z"'
        ' fill="currentColor"/></svg>'
    ),
}


def _period_icon(period: Period) -> str:
    return _PERIOD_ICONS.get(period, "")


# Supported Arabic display fonts. Each maps a name -> (Google Fonts request
# param, CSS family). Switch via AC_DISPLAY_FONT in .env — no code change.
_FONTS: dict[str, tuple[str, str]] = {
    "Cairo": ("Cairo:wght@400;600;700;900", "'Cairo'"),
    "Tajawal": ("Tajawal:wght@400;500;700;900", "'Tajawal'"),
    "Almarai": ("Almarai:wght@400;700;800", "'Almarai'"),
    "Noto Kufi Arabic": ("Noto+Kufi+Arabic:wght@400;600;700;900", "'Noto Kufi Arabic'"),
    "Noto Naskh Arabic": ("Noto+Naskh+Arabic:wght@400;500;700", "'Noto Naskh Arabic'"),
    "IBM Plex Sans Arabic": ("IBM+Plex+Sans+Arabic:wght@400;500;600;700", "'IBM Plex Sans Arabic'"),
    "Amiri": ("Amiri:wght@400;700", "'Amiri'"),
}


@dataclass(frozen=True)
class RenderContext:
    time: TimeContext
    message_text: str
    message_is_fallback: bool


def _e(text: str) -> str:
    """Escape user-supplied text before embedding in HTML."""
    return html.escape(text, quote=True)


def _resolve_font(name: str) -> tuple[str, str]:
    """Look up a font by name, tolerant of case/whitespace. Falls back to Cairo."""
    requested = name.strip().casefold()
    for key, value in _FONTS.items():
        if key.casefold() == requested:
            return value
    return _FONTS["Cairo"]


def _styles(night: bool) -> str:
    settings = get_settings()
    fg = "#fff" if night else "#000"
    bg = "#000" if night else settings.day_bg
    font_param, font_family = _resolve_font(settings.display_font)
    return f"""
@import url('https://fonts.googleapis.com/css2?family={font_param}&display=swap');
.ac-root, .ac-root * {{ margin:0; padding:0; box-sizing:border-box;
  font-family:{font_family},'Segoe UI',Tahoma,sans-serif; }}
.ac-root {{ width:800px; height:480px; overflow:hidden; direction:rtl;
  text-align:center; background:{bg}; color:{fg}; padding:22px 26px;
  display:flex; flex-direction:column; }}
/* Day-time zone — the star of the screen, ~80% of the panel height. */
.ac-root .daytime {{ flex:4 1 0; min-height:0; display:flex; flex-direction:column;
  align-items:center; justify-content:center; gap:22px; overflow:hidden; }}
.ac-root .greeting {{ font-size:120px; font-weight:900; line-height:1.02;
  display:flex; align-items:center; justify-content:center; gap:28px; }}
.ac-root .greeting .pic {{ width:104px; height:104px; flex:0 0 auto; }}
.ac-root .orient {{ font-size:46px; font-weight:700; }}
.ac-root .orient .dot {{ margin:0 16px; }}
/* Family message — the calm footer, ~20% of the panel height. */
.ac-root .message {{ flex:1 1 0; min-height:0; overflow:hidden;
  border-top:4px solid {fg}; padding-top:12px; display:flex;
  align-items:center; justify-content:center; }}
.ac-root .message-text {{ font-size:28px; font-weight:700; line-height:1.28; }}
""".strip()


def render_fragment(ctx: RenderContext) -> str:
    """Self-contained markup (scoped style + one root div) for TRMNL.

    Layout: a huge day-time greeting (period icon + Arabic weekday/date) filling
    the top ~80% of the panel so the elder can read it across the room, and the
    latest warm family message resting in the bottom ~20%.
    """
    night = ctx.time.mode is Mode.NIGHT
    return f"""<style>{_styles(night)}</style>
<div class="ac-root">
  <div class="daytime">
    <div class="greeting">{_period_icon(ctx.time.period)}{_e(ctx.time.greeting_ar)}</div>
    <div class="orient">{_e(ctx.time.weekday_ar)}<span class="dot">•</span>{_e(ctx.time.date_ar)}</div>
  </div>
  <div class="message"><div class="message-text">{_e(ctx.message_text)}</div></div>
</div>"""


def render_document(ctx: RenderContext) -> str:
    """Full HTML page wrapping the fragment — for browser previews only."""
    return (
        '<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=800, height=480">'
        "<style>body{margin:0;display:flex;justify-content:center;"
        "background:#ddd;}</style></head><body>"
        f"{render_fragment(ctx)}</body></html>"
    )
