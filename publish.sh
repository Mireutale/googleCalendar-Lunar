#!/usr/bin/env bash
# 로컬에서 .ics 빌드 → secret gist 로 발행/갱신.
# 개인정보(생일)는 GitHub public 어디에도 올라가지 않고, 추측 불가 gist URL 로만 노출.
# 최초 실행: gist 생성 후 구독 URL 출력. 이후 실행: 기존 gist 갱신.
set -euo pipefail
cd "$(dirname "$0")"

ICS="public/birthdays.ics"
GIST_ID_FILE=".gist_id"

.venv/bin/python generate.py

if [[ -f "$GIST_ID_FILE" ]]; then
  gid="$(cat "$GIST_ID_FILE")"
  gh gist edit "$gid" --filename birthdays.ics "$ICS"
  echo "갱신 완료: gist $gid"
else
  url="$(gh gist create --desc "생일 캘린더(비공개)" "$ICS")"
  gid="${url##*/}"
  echo "$gid" > "$GIST_ID_FILE"
  echo "gist 생성: $url"
fi

user="$(gh api user --jq .login)"
echo
echo "구독 URL (캘린더 앱에 붙여넣기):"
echo "https://gist.githubusercontent.com/${user}/${gid}/raw/birthdays.ics"
