#!/usr/bin/env bash
# 規約ファイルの本文が変更されている場合、改定履歴も更新されているか検証する
#
# 使い方:
#   check-revision-history.sh <BASE_REF>
#
# - BASE_REF からのdiffで terms.md/privacy.md/auth-component.md の本文が変更されている場合、
#   かつ当該ファイル内の「## 改定履歴」セクションが変更されていない場合はエラーとする

set -euo pipefail

BASE_REF="${1:-origin/main}"

cd "$(dirname "$0")/.."

if ! git rev-parse --verify "$BASE_REF" >/dev/null 2>&1; then
  echo "::warning::$BASE_REF が見つかりません。チェックをスキップします。"
  exit 0
fi

FILES=("terms.md" "privacy.md" "auth-component.md")
FAILED=0

for FILE in "${FILES[@]}"; do
  if [[ ! -f "$FILE" ]]; then continue; fi

  # そのファイルに変更があるか
  if ! git diff --quiet "$BASE_REF" -- "$FILE"; then
    # 改定履歴セクションの変更を検出
    # diff の中で "## 改定履歴" 以降の行が変更されているかを見る
    DIFF=$(git diff "$BASE_REF" -- "$FILE")
    HISTORY_CHANGED=$(echo "$DIFF" | awk '
      /^@@/ { in_hunk=1 }
      /^\+\+\+|^---/ { next }
      in_hunk && /^[+-]/ {
        line = substr($0, 2)
        if (match(line, /改定履歴/) || seen_history) {
          seen_history = 1
          if (/^[+-]/) print
        }
      }
    ')

    # より単純化: 履歴セクションに+行があるか
    HISTORY_ADDED=$(echo "$DIFF" | awk '
      BEGIN { in_history = 0 }
      /^@@/ { in_history = 0 }
      /改定履歴/ { in_history = 1 }
      in_history && /^\+[^+]/ { print }
    ')

    if [[ -z "$HISTORY_ADDED" ]]; then
      echo "::error file=$FILE::本文が変更されていますが、「## 改定履歴」に追記がありません。施行日とともに改定履歴を追記してください。"
      FAILED=1
    fi
  fi
done

if [[ "$FAILED" -ne 0 ]]; then
  echo "❌ 改定履歴の検証に失敗しました"
  exit 1
fi

echo "✅ 改定履歴の検証OK"
