#!/usr/bin/env python3
"""条文番号の連続性と相互参照の整合性を検証する。

対象: terms.md, privacy.md, auth-component.md

検査項目:
1. 「## 第N条（...）」の N が 1, 2, 3... と連続していること。
   「第N条の2」などの枝番は枝番として許容する（親の番号の連続性のみを見る）。
2. 本文中の「第N条（TITLE）」または「第N条のM（TITLE）」の TITLE が、
   同一ファイル内の実際の見出しと一致すること。
"""
from __future__ import annotations

import pathlib
import re
import sys


HEADING_RE = re.compile(r"^##\s+第(\d+)条(?:の(\d+))?[（(]([^）)]+)[）)]")
REFERENCE_RE = re.compile(r"第(\d+)条(?:の(\d+))?[（(]([^）)]+)[）)]")

FILES = ["terms.md", "privacy.md", "auth-component.md"]


def annotate(level: str, file: str, line: int, message: str) -> None:
    """GitHub Actions 形式のアノテーションを出力する。"""
    print(f"::{level} file={file},line={line}::{message}")


def check_file(path: pathlib.Path) -> int:
    """1ファイルを検査し、失敗件数を返す。"""
    failures = 0
    if not path.exists():
        annotate("warning", str(path), 1, "対象ファイルが存在しません。スキップします。")
        return 0

    lines = path.read_text(encoding="utf-8").splitlines()
    headings: dict[str, tuple[int, str]] = {}
    top_level: list[tuple[int, int, str]] = []  # (line, N, title)

    for idx, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if not m:
            continue
        n = int(m.group(1))
        sub = m.group(2)
        title = m.group(3)
        key = f"{n}" if sub is None else f"{n}.{sub}"
        headings[key] = (idx, title)
        if sub is None:
            top_level.append((idx, n, title))

    # 連続性チェック
    expected = 1
    for line_no, n, title in top_level:
        if n != expected:
            annotate(
                "error",
                str(path),
                line_no,
                f"条文番号が連続していません (期待: 第{expected}条, 実際: 第{n}条「{title}」)",
            )
            failures += 1
            expected = n  # 以降の検出を続けるためにリセット
        expected = n + 1

    # 相互参照チェック
    for idx, line in enumerate(lines, start=1):
        if HEADING_RE.match(line):
            # 見出し行自体は除外
            continue
        for match in REFERENCE_RE.finditer(line):
            n = match.group(1)
            sub = match.group(2)
            ref_title = match.group(3)
            key = n if sub is None else f"{n}.{sub}"

            actual = headings.get(key)
            if actual is None:
                # 他ファイルへの参照の可能性があるので warning に留める
                annotate(
                    "warning",
                    str(path),
                    idx,
                    f"第{key.replace('.', 'の')}条の見出しが同一ファイルに見つかりません (参照: 「{ref_title}」)",
                )
                continue

            if actual[1] != ref_title:
                annotate(
                    "error",
                    str(path),
                    idx,
                    f"相互参照の見出し不一致 (参照:「{ref_title}」, 実際:「{actual[1]}」 on L{actual[0]})",
                )
                failures += 1

    return failures


def main() -> int:
    total_failures = 0
    for name in FILES:
        total_failures += check_file(pathlib.Path(name))

    if total_failures:
        print(f"❌ 条文番号・相互参照の検証に失敗しました (エラー {total_failures} 件)")
        return 1

    print("✅ 条文番号・相互参照の検証OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
