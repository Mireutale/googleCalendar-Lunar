import unittest
from datetime import date

from generate import build


class BuildAnniversaryCalendarTest(unittest.TestCase):
    def test_generates_annual_and_milestone_events(self):
        cfg = {
            "settings": {
                "years_ahead": 2,
                "reminder_days": 0,
                "calendar_name": "기념일",
                "title_format": "🎂 {name} 생일",
            },
            "people": [],
            "annual_events": [
                {
                    "name": "부모님 결혼 기념일",
                    "title": "부모님 결혼 기념일 💍",
                    "type": "solar",
                    "date": "10-29",
                }
            ],
            "milestones": [
                {
                    "name": "기념일",
                    "start_date": "2026-06-24",
                    "every_days": 100,
                    "yearly": True,
                    "day_title_format": "{days}일 ❤️",
                    "anniversary_title_format": "❤️ {years}주년",
                }
            ],
        }

        ics = build(cfg, date(2026, 7, 16))

        self.assertIn("X-WR-CALNAME:기념일", ics)
        self.assertIn("DTSTART;VALUE=DATE:20260624", ics)
        self.assertIn("SUMMARY:1일 ❤️", ics)
        self.assertIn("DTSTART;VALUE=DATE:20261001", ics)
        self.assertIn("SUMMARY:100일 ❤️", ics)
        self.assertIn("DTSTART;VALUE=DATE:20270624", ics)
        self.assertIn("SUMMARY:❤️ 1주년", ics)
        self.assertIn("DTSTART;VALUE=DATE:20261029", ics)
        self.assertIn("SUMMARY:부모님 결혼 기념일 💍", ics)


if __name__ == "__main__":
    unittest.main()
