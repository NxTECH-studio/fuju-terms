#!/usr/bin/env bash
# 条文番号の連続性と相互参照の整合性を検証する
#
# 対象: terms.md, privacy.md, auth-component.md
# - 「## 第N条（...）」の N が 1,2,3... と連続していること（「第N条の2」は枝番として許容）
# - 本文中の「第N条（TITLE）」または「第N条のM（TITLE）」の TITLE が、同一ファイル内の実際の見出しと一致すること

set -euo pipefail

cd "$(dirname "$0")/.."

if ! command -v python3 >/dev/null 2>&1; then
  echo "::error::python3 が必要です"
  exit 1
fi

python3 "$(dirname "$0")/check_articles.py" "$@"
