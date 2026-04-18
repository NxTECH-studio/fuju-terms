#!/usr/bin/env python3
"""原作ガイドラインページをヘッドレスブラウザで取得し、本文テキストを標準出力に書き出す。

使い方:
    python3 fetch_guideline.py <URL>

Playwright が必要。GitHub Actions では microsoft/playwright-github-action 相当を使う。
"""
from __future__ import annotations

import re
import sys

from playwright.sync_api import sync_playwright


def normalize(text: str) -> str:
    """日付・キャッシュバスターなど変動要素を正規化する。"""
    # 連続する空白を1つに
    text = re.sub(r"\s+", " ", text).strip()
    # よくある自動生成のトラッキング番号 (8桁以上の数値列) を除去
    text = re.sub(r"\b\d{8,}\b", "<NUM>", text)
    return text


def main(url: str) -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until="networkidle", timeout=60_000)
        # 動的ロードを待つ
        page.wait_for_timeout(2_000)
        # 本文領域の特定を試みる。見つからなければ body 全体。
        content = ""
        for selector in ["main", "article", ".detail", "#detail", "body"]:
            try:
                el = page.query_selector(selector)
                if el:
                    content = el.inner_text()
                    break
            except Exception:
                continue
        browser.close()

    if not content.strip():
        print("ERROR: 本文テキストを取得できませんでした", file=sys.stderr)
        return 1

    print(normalize(content))
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: fetch_guideline.py <URL>", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
