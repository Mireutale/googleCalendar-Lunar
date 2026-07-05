"""birthdays.yaml -> birthdays.ics 생성.

음력 생일은 매년 양력 날짜가 달라 RRULE로 반복 불가.
=> 연도별 양력 날짜를 계산해 개별 이벤트로 생성.

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


def lunar_to_solar(birth: date, leap: bool, target_year: int):
    """target_year의 음력 생일(KASI)에 해당하는 양력 날짜. 없거나 범위 밖이면 None."""
    month, day = birth.month, birth.day
    for use_leap in ([leap, False] if leap else [False]):
        for d in (day, 29, 28):  # 윤달 부재/30일 없는 달 대비 fallback
            if _cal.setLunarDate(target_year, month, d, use_leap):
                return date.fromisoformat(_cal.SolarIsoFormat())
    return None


def solar_in_year(birth: date, target_year: int):
    try:
        return birth.replace(year=target_year)
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


def event(name: str, ev_date: date, age: int, cfg: dict, uid: str) -> list:
    title = cfg["title_format"].format(name=name, age=age)
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
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//googleCalendar-Lunar//KR",
        "CALSCALE:GREGORIAN",
        "X-WR-CALNAME:생일",
        "X-WR-TIMEZONE:Asia/Seoul",
    ]
    for i, p in enumerate(cfg["people"]):
        birth = p["date"] if isinstance(p["date"], date) else date.fromisoformat(str(p["date"]))
        ptype = p["type"]
        leap = bool(p.get("leap_month", False))
        for y in range(today.year, today.year + years + 1):
            ev = lunar_to_solar(birth, leap, y) if ptype == "lunar" else solar_in_year(birth, y)
            if ev is None or ev < today:
                continue
            age = y - birth.year
            uid = f"{i}-{ptype}-{y}@lunar-birthday"
            out += event(p["name"], ev, age, s, uid)
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
