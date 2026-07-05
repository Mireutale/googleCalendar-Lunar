# googleCalendar-Lunar

음력·양력 생일을 하나의 캘린더 구독(`.ics`)으로 자동 생성.
**음력 생일**은 매년 양력 날짜가 바뀌어 일반 반복 일정으로 불가 → 연도별 양력 날짜를 계산해 개별 이벤트로 만든다.

- 설정은 `birthdays.yaml` **한 파일만** 수정
- GitHub Actions가 매년 1/1(한국시각) 자동으로 다음 1년치 롤링 갱신 + yaml 수정 push 시 즉시 재생성
- GitHub Pages가 `birthdays.ics`를 URL로 서빙 → Notion Calendar / Google Calendar에서 **URL 구독**

구독 URL (`<사용자명>` = **본인 GitHub 아이디**):
```
https://<사용자명>.github.io/googleCalendar-Lunar/birthdays.ics
```

> 이 저장소는 원본이라 다른 사람은 push할 수 없다.
> **각자 Fork 떠서 본인 저장소에서** 생일을 관리하고, 위 URL의 `<사용자명>`도 본인 아이디로 바꿔 쓴다.

---

## 최초 1회 세팅

1. **Fork**
   이 저장소 우상단 **Fork** → 본인 계정으로 복사. 이후 모든 작업은 **본인 Fork**에서 한다.

2. **GitHub Pages 켜기**
   본인 Fork → **Settings → Pages → Build and deployment → Source** 를 **GitHub Actions** 로 선택.

3. **Actions 활성화**
   Fork한 저장소는 Actions가 기본 비활성일 수 있음. **Actions 탭 → "I understand my workflows, go ahead and enable them"** 클릭.

4. **첫 배포 실행**
   `birthdays.yaml` 을 실제 생일로 수정 후 push. (또는 **Actions 탭 → Build & Deploy → Run workflow** 수동 실행)
   초록불 뜨면 `https://<본인아이디>.github.io/googleCalendar-Lunar/birthdays.ics` 접속해 `.ics` 내용 확인.

5. **캘린더 앱에서 구독** (아래)

---

## 사용법 — 생일 추가/수정

`birthdays.yaml` 만 고치고 push 하면 끝.

```yaml
settings:
  years_ahead: 50                              # 오늘부터 몇 년치 생성
  all_day: true                                # 종일 일정
  reminder_days: 1                             # 며칠 전 알림 (0=당일)
  title_format: "🎂 {name} 생일 ({age}세)"    # {name}=이름, {age}=해당연도-출생연도

people:
  - name: 엄마
    type: lunar          # lunar=음력 / solar=양력
    date: 1965-03-15     # 출생일 YYYY-MM-DD (음력이면 음력 날짜 그대로)
    leap_month: false    # 음력 윤달이면 true (양력은 생략 가능)

  - name: 나
    type: solar
    date: 1995-08-20
```

| 필드 | 설명 |
|------|------|
| `type` | `lunar`(음력) 또는 `solar`(양력) |
| `date` | 출생일. 음력이면 **음력 날짜 그대로** 적는다 |
| `leap_month` | 음력 윤달 출생만 `true` |
| `years_ahead` | 미래 몇 년치 생성할지 |
| `reminder_days` | 알림 며칠 전 (`0`=당일 아침) |
| `title_format` | 일정 제목. `{name}`, `{age}` 치환 |

수정 → `git add . && git commit -m "생일 수정" && git push` → 자동 재생성·배포.

---

## 캘린더 앱에서 구독하기

### Notion Calendar
왼쪽 캘린더 목록 옆 **+ (Add calendar) → Subscribe by URL** 에 구독 URL 붙여넣기.

### Google Calendar
좌측 **다른 캘린더 → + → URL로 추가** 에 구독 URL 붙여넣기.
Google Calendar를 Notion Calendar 계정에 연결해 두면 Notion에도 함께 표시됨.

> 구독형은 앱이 주기적으로(보통 몇 시간~하루) URL을 다시 읽어 갱신한다.
> 생성 자체는 GitHub이 1년에 한 번 하지만, 파일에 미래 50년치가 들어있어 언제 읽어도 전부 보인다.

---

## 자동 갱신 주기

`.github/workflows/build.yml`:
- `cron: "0 15 31 12 *"` → 매년 12/31 15:00 UTC = **한국 1/1 00:00** 재생성(롤링)
- `birthdays.yaml`/`generate.py` push 시 즉시 재생성
- Actions 탭에서 **수동 실행**도 가능

---

## 음력 처리 주의

- 음력→양력 변환은 **한국천문연구원(KASI)** 데이터 기반 [`korean_lunar_calendar`](https://pypi.org/project/korean-lunar-calendar/) 사용.
  중국 음력은 자오선(UTC+8) 차이로 한국(UTC+9)과 **하루씩 어긋나는 날짜가 존재**해(예: 음력 2020년 2월 전체가 하루 밀림) 한국 기준으로 계산한다.
- **KASI 데이터 상한은 양력 2050-12-31.** 그 이후 음력 생일은 자동으로 건너뛴다(양력 생일은 제한 없음).
  즉 `years_ahead`를 크게 잡아도 음력은 2050년까지만 생성됨.
- 특정 해에 **윤달이 없거나** 해당 음력 달에 **30일이 없으면**, 평달·29일·28일 순으로 대체한다.

---

## 로컬 실행 (선택)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python generate.py   # -> public/birthdays.ics
```
