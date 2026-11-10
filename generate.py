"""birthdays.yaml -> birthdays.ics 기념일 캘린더 생성.

음력 생일은 매년 양력 날짜가 달라 RRULE로 반복 불가.
=> 연도별 양력 날짜를 계산해 개별 이벤트로 생성.

고정 기념일과 기준일로부터 100일 단위/주년 일정도 함께 생성한다.

음력 변환은 한국천문연구원(KASI) 데이터 기반 korean_lunar_calendar 사용.
(중국 음력과 자오선 차이로 하루씩 어긋나는 날짜가 있어 한국 기준을 쓴다.)
KASI 데이터 상한은 양력 2050-12-31 → 이후 음력 생일은 자동 skip.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import yaml
from korean_lunar_calendar import KoreanLunarCalendar

CONFIG_PATH = Path(__file__).parent / "birthdays.yaml"
EXAMPLE_PATH = Path(__file__).parent / "birthdays.example.yaml"
OUTPUT_PATH = Path(__file__).parent / "public" / "birthdays.ics"

_cal = KoreanLunarCalendar()


def parse_md(raw) -> tuple[int, int]:
    """date 필드 -> (month, day). YYYY-MM-DD / MM-DD / date 객체 모두 허용."""
    if isinstance(raw, date):
        return raw.month, raw.day
    parts = str(raw).split("-")
    m, d = parts[-2], parts[-1]  # 연도 유무 무관하게 뒤 두 개
    return int(m), int(d)


def parse_date(raw) -> date:
    """YYYY-MM-DD 문자열 또는 YAML date 객체를 date로 변환."""
    if isinstance(raw, date):
        return raw
    return date.fromisoformat(str(raw))


def lunar_to_solar(month: int, day: int, leap: bool, target_year: int):
    """target_year의 음력 생일(KASI)에 해당하는 양력 날짜. 없거나 범위 밖이면 None."""
    for use_leap in ([leap, False] if leap else [False]):
        for d in (day, 29, 28):  # 윤달 부재/30일 없는 달 대비 fallback
            if _cal.setLunarDate(target_year, month, d, use_leap):
                return date.fromisoformat(_cal.SolarIsoFormat())
    return None


def solar_in_year(month: int, day: int, target_year: int):
    try:
        return date(target_year, month, day)
    except ValueError:  # 2/29 -> 평년
        return date(target_year, 2, 28)


def fold(line: str) -> str:
    """RFC5545: 75옥텟 초과 라인 접기."""
    if len(line.encode("utf-8")) <= 75:
        return line
    out, cur = [], b""
    for ch in line:
        e = ch.encode("utf-8")
        if len(cur) + len(e) > 74:
            out.append(cur.decode("utf-8"))
            cur = b" " + e
        else:
            cur += e
    out.append(cur.decode("utf-8"))
    return "\r\n".join(out)


def event(title: str, ev_date: date, cfg: dict, uid: str) -> list:
    end = ev_date + timedelta(days=1)
    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTART;VALUE=DATE:{ev_date:%Y%m%d}",
        f"DTEND;VALUE=DATE:{end:%Y%m%d}",
        f"SUMMARY:{title}",
        "TRANSP:TRANSPARENT",
    ]
    r = int(cfg.get("reminder_days", 0))
    if r > 0:
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"TRIGGER:-P{r}D",
            f"DESCRIPTION:{title}",
            "END:VALARM",
        ]
    lines.append("END:VEVENT")
    return lines


def build(cfg: dict, today: date) -> str:
    s = cfg["settings"]
    years = int(s["years_ahead"])
    last_date = date(today.year + years, 12, 31)
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//googleCalendar-Lunar//KR",
        "CALSCALE:GREGORIAN",
        f"X-WR-CALNAME:{s.get('calendar_name', '기념일')}",
        "X-WR-TIMEZONE:Asia/Seoul",
    ]
    for i, p in enumerate(cfg.get("people", [])):
        month, day = parse_md(p["date"])
        ptype = p["type"]
        leap = bool(p.get("leap_month", False))
        for y in range(today.year, today.year + years + 1):
            ev = lunar_to_solar(month, day, leap, y) if ptype == "lunar" else solar_in_year(month, day, y)
            if ev is None or ev < today:
                continue
            uid = f"{i}-{ptype}-{y}@lunar-birthday"
            title = s["title_format"].format(name=p["name"])
            out += event(title, ev, s, uid)

    for i, anniversary in enumerate(cfg.get("annual_events", [])):
        month, day = parse_md(anniversary["date"])
        event_type = anniversary.get("type", "solar")
        leap = bool(anniversary.get("leap_month", False))
        title = anniversary.get("title", anniversary["name"])
        for y in range(today.year, today.year + years + 1):
            ev = (
                lunar_to_solar(month, day, leap, y)
                if event_type == "lunar"
                else solar_in_year(month, day, y)
            )
            if ev is None or ev < today:
                continue
            uid = f"annual-{i}-{event_type}-{y}@lunar-birthday"
            out += event(title, ev, s, uid)

    for i, milestone in enumerate(cfg.get("milestones", [])):
        start = parse_date(milestone["start_date"])
        if start > last_date:
            continue

        name = milestone.get("name", "")
        day_title_format = milestone.get("day_title_format", "{days}일")
        anniversary_title_format = milestone.get("anniversary_title_format", "{years}주년")

        title = day_title_format.format(name=name, days=1)
        out += event(title, start, s, f"milestone-{i}-days-1@lunar-birthday")

        every_days = int(milestone.get("every_days", 0))
        if every_days > 0:
            days = every_days
            while True:
                # 시작일을 1일째로 세므로 N일은 시작일 + (N - 1)일이다.
                ev = start + timedelta(days=days - 1)
                if ev > last_date:
                    break
                title = day_title_format.format(name=name, days=days)
                out += event(title, ev, s, f"milestone-{i}-days-{days}@lunar-birthday")
                days += every_days

        if milestone.get("yearly", False):
            for y in range(start.year + 1, last_date.year + 1):
                ev = solar_in_year(start.month, start.day, y)
                if ev > last_date:
                    break
                years_since = y - start.year
                title = anniversary_title_format.format(name=name, years=years_since)
                out += event(title, ev, s, f"milestone-{i}-years-{years_since}@lunar-birthday")

    out.append("END:VCALENDAR")
    return "\r\n".join(fold(l) for l in out) + "\r\n"


def main() -> None:
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    ics = build(cfg, date.today())
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(ics, encoding="utf-8")
    print(f"생성 완료: {OUTPUT_PATH} ({ics.count('BEGIN:VEVENT')} events)")


if __name__ == "__main__":
    main()
