"""Quick offline smoke test — no server needed.

Run:  ./.venv/Scripts/python.exe smoke_test.py
Writes preview_day.html and preview_night.html you can open in a browser.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from app.time_context import Mode, Period, build_time_context
from app.bible import SEED_VERSES
from app.renderer import RenderContext, render_document
from app.models import Task, TaskPeriod, Event

tz = "Asia/Jerusalem"


def preview(hour: int, filename: str) -> None:
    now = datetime(2026, 7, 8, hour, 0, tzinfo=ZoneInfo(tz))
    tc = build_time_context(tz, now=now)
    ctx = RenderContext(
        time=tc,
        message_text="مرحباً يا جدّتي الغالية، سارة قادمة لزيارتك اليوم الساعة الثالثة عصراً ومعها الأولاد، ننتظر لقاءك بفارغ الصبر ونحبّك كثيراً",
        message_is_fallback=False,
        tasks=[
            Task(id=1, title="تناول دواء الصباح", period=TaskPeriod.MORNING,
                 done=True, created_at=now),
            Task(id=2, title="تناول الغداء", period=TaskPeriod.ANYTIME,
                 done=False, created_at=now),
            Task(id=3, title="شرب الماء", period=TaskPeriod.ANYTIME,
                 done=False, created_at=now),
        ],
        events=[
            Event(id=1, title="زيارة يوسف", event_date="2026-07-08",
                  time_text="حوالي الساعة ٥ مساءً", created_at=now),
            Event(id=2, title="وصول الممرضة", event_date="2026-07-08",
                  time_text="بعد الظهر", created_at=now),
        ],
        verse=SEED_VERSES[now.timetuple().tm_yday % len(SEED_VERSES)],
    )
    with open(filename, "w", encoding="utf-8") as fh:
        fh.write(render_document(ctx))
    print(f"  hour={hour:>2}  period={tc.period.value:<9} mode={tc.mode.value:<5} "
          f"greeting={tc.greeting_ar}  ->  {filename}")


def assert_time_logic() -> None:
    def ctx(h):
        return build_time_context(tz, now=datetime(2026, 7, 8, h, 0, tzinfo=ZoneInfo(tz)))
    assert ctx(4).period is Period.MORNING and ctx(4).mode is Mode.DAY   # new 04:00 start
    assert ctx(3).period is Period.NIGHT and ctx(3).mode is Mode.NIGHT   # 03:59 still night
    assert ctx(8).period is Period.MORNING and ctx(8).mode is Mode.DAY
    assert ctx(14).period is Period.AFTERNOON and ctx(14).mode is Mode.DAY
    assert ctx(18).period is Period.EVENING and ctx(18).mode is Mode.DAY
    assert ctx(22).period is Period.NIGHT and ctx(22).mode is Mode.NIGHT
    assert ctx(8).weekday_ar == "الأربعاء"  # 2026-07-08 is a Wednesday
    print("  time logic assertions: OK")


if __name__ == "__main__":
    print("Time-of-day logic:")
    assert_time_logic()
    print("Rendering previews:")
    preview(9, "preview_day.html")
    preview(22, "preview_night.html")
    print("Done.")
