#!/usr/bin/env python3
"""Fail if a link to an iotype.com service page uses a generic anchor.

Why: iotype.com has consumer-facing pages for the same services (voice typing,
OCR, translation...). If this repository links to the *developer* pages using
the bare service name, the two compete for the same search query and neither
ranks well. Every anchor pointing at a service page must name the API or
وب‌سرویس explicitly.

    BAD   [Persian OCR](https://iotype.com/api-service/ocr)
    GOOD  [Persian OCR API](https://iotype.com/api-service/ocr)

    BAD   [تایپ صوتی همزمان](https://iotype.com/api-service/speech-to-text)
    GOOD  [وب سرویس تایپ صوتی همزمان](https://iotype.com/api-service/speech-to-text)

Links to the homepage (https://iotype.com) are exempt — brand anchors cannot
cannibalise a service page.
"""

from __future__ import annotations

import pathlib
import re
import sys

LINK = re.compile(r"\[([^\]\n]+)\]\((https://iotype\.com/[^)]+)\)")

# A "link" inside backticks is an example, not a real link — the docs quote
# both good and bad anchors. Blank out inline code before matching.
INLINE_CODE = re.compile(r"`[^`]*`")

# An anchor qualifies if it contains any of these, case-insensitively.
QUALIFIERS = ("api", "وب سرویس", "وب‌سرویس", "web service", "endpoint", "sdk")

# Anchors that are allowed to be bare: the literal URL, and brand names.
EXEMPT = {
    "iotype.com/api-service",
    "iotype.com/plans/api",
    "iotype",
    "**iotype**",
    "iotype.com",
    "آی او تایپ",
    "**آی او تایپ**",
}


def main() -> int:
    root = pathlib.Path(__file__).resolve().parents[2]
    problems: list[str] = []

    for path in sorted(root.rglob("*.md")):
        if any(part in {"node_modules", "vendor", "dist"} for part in path.parts):
            continue
        in_fence = False
        for lineno, line in enumerate(path.read_text().splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for label, url in LINK.findall(INLINE_CODE.sub("", line)):
                if label.startswith("!"):          # badge image
                    continue
                if label in EXEMPT:
                    continue
                if any(q in label.lower() for q in QUALIFIERS):
                    continue
                rel = path.relative_to(root)
                problems.append(f"{rel}:{lineno}  [{label}]({url})")

    if problems:
        print("Generic anchor text pointing at an iotype.com service page.")
        print("Add 'API' or 'وب سرویس' to the anchor so it does not compete")
        print("with the consumer-facing page for the same query.\n")
        for p in problems:
            print(f"  {p}")
        print(f"\n{len(problems)} problem(s).")
        return 1

    print("All anchors to iotype.com service pages are API-qualified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
