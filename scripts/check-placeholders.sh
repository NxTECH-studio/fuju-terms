#!/usr/bin/env bash
# プレースホルダーの一貫性を検証する
#
# - 全Markdownファイルに出現する {{...}} 形式のプレースホルダーを抽出
# - README.md のプレースホルダー一覧（許可リスト）に載っていないものを検出
# - 逆に README で定義されているのに一度も使われていないプレースホルダーも警告

set -euo pipefail

cd "$(dirname "$0")/.."

# 許可リストを README から抽出: バッククォートで囲まれた {{...}}
ALLOWED=$(grep -oE '`{{[^}]+}}`' README.md | sed -e 's/`//g' | sort -u)

if [[ -z "$ALLOWED" ]]; then
  echo "::error file=README.md::プレースホルダー一覧を README.md から抽出できませんでした"
  exit 1
fi

echo "== 許可されているプレースホルダー =="
echo "$ALLOWED"
echo ""

FAILED=0

# 全ての .md ファイルを走査
for FILE in terms.md privacy.md auth-component.md; do
  if [[ ! -f "$FILE" ]]; then continue; fi

  # コードブロック内のプレースホルダーは対象外にしたいが、
  # 簡易実装として全行から抽出
  USED=$(grep -oE '\{\{[^}]+\}\}' "$FILE" | sort -u || true)
  for P in $USED; do
    if ! echo "$ALLOWED" | grep -Fxq "$P"; then
      LINE=$(grep -nF "$P" "$FILE" | head -1 | cut -d: -f1)
      echo "::error file=$FILE,line=${LINE:-1}::許可されていないプレースホルダー: ${P} (README.md のプレースホルダー一覧に追加するか、使用箇所を修正してください)"
      FAILED=1
    fi
  done
done

# 許可リストにあるが一度も使われていないもの
for P in $ALLOWED; do
  if ! grep -rFq "$P" terms.md privacy.md auth-component.md 2>/dev/null; then
    echo "::warning file=README.md::プレースホルダー ${P} は README で定義されていますが、どのドキュメントでも使われていません"
  fi
done

if [[ "$FAILED" -ne 0 ]]; then
  echo "❌ プレースホルダー検証に失敗しました"
  exit 1
fi

echo "✅ プレースホルダー検証OK"
