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
  * Three stark orientation lines up top, a simple visual checklist, one warm
    family message, today's visits, and a comforting verse. No clock, no
    minutes, no clutter.
"""
from __future__ import annotations

import html
from dataclasses import dataclass

from .bible import Verse
from .config import get_settings
from .models import Event, Task
from .time_context import Mode, TimeContext


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
    tasks: list[Task]
    events: list[Event]
    verse: Verse | None


def _e(text: str) -> str:
    """Escape user-supplied text before embedding in HTML."""
    return html.escape(text, quote=True)


def _styles(night: bool) -> str:
    settings = get_settings()
    fg = "#fff" if night else "#000"
    bg = "#000" if night else settings.day_bg
    font_param, font_family = _FONTS.get(settings.display_font, _FONTS["Cairo"])
    return f"""
@import url('https://fonts.googleapis.com/css2?family={font_param}&display=swap');
.ac-root, .ac-root * {{ margin:0; padding:0; box-sizing:border-box;
  font-family:{font_family},'Segoe UI',Tahoma,sans-serif; }}
.ac-root {{ width:800px; height:480px; overflow:hidden; direction:rtl;
  text-align:right; background:{bg}; color:{fg}; padding:18px 22px;
  display:flex; flex-direction:column; }}
.ac-root .header {{ flex:0 0 auto; text-align:center; border-bottom:4px solid {fg};
  padding-bottom:8px; margin-bottom:12px; }}
.ac-root .greeting {{ font-size:58px; font-weight:900; line-height:1.05; }}
.ac-root .orient {{ font-size:28px; font-weight:700; margin-top:4px; }}
.ac-root .orient .dot {{ margin:0 12px; }}
.ac-root .body {{ display:flex; flex:1 1 auto; gap:18px; min-height:0;
  overflow:hidden; }}
.ac-root .col {{ display:flex; flex-direction:column; min-height:0;
  overflow:hidden; }}
.ac-root .col-side {{ flex:0 0 290px; }}
.ac-root .col-main {{ flex:1 1 auto; }}
.ac-root .checklist {{ list-style:none; overflow:hidden; }}
.ac-root .checklist li {{ display:flex; align-items:center; gap:10px;
  font-size:26px; font-weight:600; margin-bottom:9px; }}
.ac-root .checkbox {{ flex:0 0 30px; width:30px; height:30px;
  border:3px solid {fg}; display:flex; align-items:center;
  justify-content:center; font-size:22px; font-weight:900; }}
.ac-root .checkbox.done {{ background:{fg}; color:{bg}; }}
.ac-root .task-text.done-text {{ text-decoration:line-through; opacity:.75; }}
.ac-root .message-box {{ flex:1 1 auto; min-height:0; overflow:hidden;
  display:flex; align-items:center; justify-content:center; text-align:center;
  padding:18px; }}
.ac-root .message-text {{ font-size:34px; font-weight:700; line-height:1.4; }}
.ac-root .visits {{ flex:0 0 auto; list-style:none; margin-top:12px;
  padding-top:12px; border-top:3px solid {fg}; }}
.ac-root .visits li {{ font-size:22px; font-weight:700; line-height:1.35;
  margin-bottom:6px; list-style:none; }}
.ac-root .visits li::before {{ content:''; display:inline-block; width:11px;
  height:11px; background:{fg}; margin-left:10px; vertical-align:baseline; }}
.ac-root .event-when {{ font-weight:400; }}
.ac-root .empty {{ font-size:20px; opacity:.7; }}
.ac-root .footer {{ flex:0 0 auto; border-top:4px solid {fg}; margin-top:10px;
  padding-top:8px; text-align:center; }}
.ac-root .verse {{ font-size:28px; font-weight:600; }}
.ac-root .verse-ref {{ font-size:20px; opacity:.75; margin-top:2px; }}
""".strip()


def _checklist(tasks: list[Task]) -> str:
    if not tasks:
        return '<p class="empty">لا توجد مهام الآن — استرِح واستمتع بيومك</p>'
    items = []
    for task in tasks:
        box = "checkbox done" if task.done else "checkbox"
        mark = "✓" if task.done else ""
        title_cls = "done-text" if task.done else ""
        items.append(
            f'<li><span class="{box}">{mark}</span>'
            f'<span class="task-text {title_cls}">{_e(task.title)}</span></li>'
        )
    return f'<ul class="checklist">{"".join(items)}</ul>'


def _visits(events: list[Event]) -> str:
    """Visits as plain lines (no label). Empty -> nothing at all."""
    if not events:
        return ""
    items = []
    for ev in events:
        when = (
            f' <span class="event-when">— {_e(ev.time_text)}</span>'
            if ev.time_text else ""
        )
        items.append(
            f'<li><span class="event-title">{_e(ev.title)}</span>{when}</li>'
        )
    return f'<ul class="visits">{"".join(items)}</ul>'


def render_fragment(ctx: RenderContext) -> str:
    """Self-contained markup (scoped style + one root div) for TRMNL.

    Layout: left rail = task checklist + today's visits (visually separated,
    no text labels). Right = the family message using the full column height so
    even a long note stays fully readable. Footer = the verse.
    """
    night = ctx.time.mode is Mode.NIGHT
    return f"""<style>{_styles(night)}</style>
<div class="ac-root">
  <div class="header">
    <div class="greeting">{ctx.time.greeting_emoji} {_e(ctx.time.greeting_ar)}</div>
    <div class="orient">{_e(ctx.time.weekday_ar)}<span class="dot">•</span>{_e(ctx.time.date_ar)}</div>
  </div>
  <div class="body">
    <div class="col col-side">
      {_checklist(ctx.tasks)}
      {_visits(ctx.events)}
    </div>
    <div class="col col-main">
      <div class="message-box"><div class="message-text">{_e(ctx.message_text)}</div></div>
    </div>
  </div>
  {_footer(ctx.verse)}
</div>"""


def _footer(verse: Verse | None) -> str:
    if verse is None:
        return ""
    ref = f'<div class="verse-ref">{_e(verse.reference)}</div>' if verse.reference else ""
    return (
        f'<div class="footer"><div class="verse">"{_e(verse.text)}"</div>{ref}</div>'
    )


def render_document(ctx: RenderContext) -> str:
    """Full HTML page wrapping the fragment — for browser previews only."""
    return (
        '<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=800, height=480">'
        "<style>body{margin:0;display:flex;justify-content:center;"
        "background:#ddd;}</style></head><body>"
        f"{render_fragment(ctx)}</body></html>"
    )
