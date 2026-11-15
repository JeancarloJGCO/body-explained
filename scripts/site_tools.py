#!/usr/bin/env python3
"""Utilities for The Body Explained.

  python3 scripts/site_tools.py check <file.md>   -> quality gate for one article (exit 1 if it fails)
  python3 scripts/site_tools.py check-all         -> run the quality gate on every article
  python3 scripts/site_tools.py registry          -> rebuild data/articles-registry.xlsx and .csv

Requires: pyyaml, openpyxl  (pip install pyyaml openpyxl)
"""
import csv, datetime as dt, os, re, sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ARTICLES = ROOT / "src" / "content" / "articles"
DATA = ROOT / "data"
SITE_URL = os.environ.get("SITE_URL", "https://the-body-explained.netlify.app").rstrip("/")

CATEGORIES = {
    "how-the-body-works": "How the Body Works",
    "sleep": "Sleep",
    "nutrition-basics": "Nutrition Basics",
    "movement": "Movement & Fitness",
    "mind": "Mind & Brain",
    "everyday-health": "Everyday Health Questions",
}

# Phrases that signal off-limits medical content (dosing, treatment advice, miracle claims).
FORBIDDEN = [
    r"\b(cures?|heals?|reverses?) (cancer|diabetes|disease|anxiety|depression|arthritis)\b", r"\bmiracle\b", r"\bdetox\b", r"\bguaranteed\b",
    r"\b\d+\s?mg\b(?=[^.]*\b(take|dose|dosage)\b)", r"\bstop taking\b", r"\bstart taking\b",
    r"\binstead of (your|seeing a) doctor\b",
]

MIN_WORDS = 1000  # body + FAQ answers
MIN_H2 = 4
MIN_SOURCES = 3
MIN_FAQ = 3


def load(path: Path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path.name}: missing frontmatter")
    return yaml.safe_load(m.group(1)), m.group(2)


def words(body: str) -> int:
    clean = re.sub(r"[#>*|`_\-\[\]()]", " ", body)
    return len(re.findall(r"[A-Za-z0-9']+", clean))


def check(path: Path, others=None) -> list[str]:
    errs = []
    fm, body = load(path)
    slug = path.stem
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        errs.append("slug must be lowercase-kebab-case")
    t = fm.get("title", "")
    if not t or len(t) > 80:
        errs.append("title missing or > 80 chars")
    d = fm.get("description", "")
    if not (80 <= len(d) <= 170):
        errs.append(f"description must be 80-170 chars (is {len(d)})")
    if fm.get("category") not in CATEGORIES:
        errs.append(f"category must be one of {list(CATEGORIES)}")
    if len(fm.get("keywords") or []) < 3:
        errs.append("need at least 3 keywords")
    if len(fm.get("sources") or []) < MIN_SOURCES:
        errs.append(f"need at least {MIN_SOURCES} sources")
    for s in fm.get("sources") or []:
        if not str(s.get("url", "")).startswith("https://"):
            errs.append(f"source url must be https: {s.get('url')}")
    if len(fm.get("faq") or []) < MIN_FAQ:
        errs.append(f"need at least {MIN_FAQ} FAQ items")
    n = words(body) + sum(words(x.get("a", "")) for x in (fm.get("faq") or []))
    if n < MIN_WORDS:
        errs.append(f"body has {n} words, minimum is {MIN_WORDS}")
    h2 = len(re.findall(r"^## ", body, re.M))
    if h2 < MIN_H2:
        errs.append(f"need at least {MIN_H2} H2 sections (has {h2})")
    if "> **In short:**" not in body:
        errs.append("missing '> **In short:**' summary box")
    if "## The takeaway" not in body:
        errs.append("missing '## The takeaway' section")
    low = body.lower()
    for pat in FORBIDDEN:
        if re.search(pat, low):
            errs.append(f"forbidden pattern found: {pat}")
    if others:
        for o_slug, o_title in others:
            if o_slug != slug and o_title.strip().lower() == t.strip().lower():
                errs.append(f"duplicate title with {o_slug}")
    return errs


def all_articles():
    return sorted(ARTICLES.glob("*.md"))


def cmd_check(paths):
    meta = [(p.stem, load(p)[0].get("title", "")) for p in all_articles()]
    bad = 0
    for p in paths:
        errs = check(p, meta)
        if errs:
            bad += 1
            print(f"FAIL {p.name}")
            for e in errs:
                print(f"   - {e}")
        else:
            print(f"PASS {p.name} ({words(load(p)[1])} words)")
    return 1 if bad else 0


def cmd_registry():
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    rows = []
    for p in all_articles():
        fm, body = load(p)
        pub = fm["publishDate"]
        pub = pub.isoformat() if isinstance(pub, (dt.date, dt.datetime)) else str(pub)
        rows.append({
            "Published": pub[:10],
            "Title": fm["title"],
            "URL": f"{SITE_URL}/articles/{p.stem}/",
            "Category": CATEGORIES.get(fm["category"], fm["category"]),
            "Main keyword": (fm.get("keywords") or [""])[0],
            "All keywords": ", ".join(fm.get("keywords") or []),
            "Words": words(body),
            "Read min": fm.get("readingMinutes"),
            "Sources": len(fm.get("sources") or []),
            "Status": "Draft" if fm.get("draft") else "Published",
            "Slug": p.stem,
        })
    rows.sort(key=lambda r: (r["Published"], r["Slug"]))
    for i, r in enumerate(rows, 1):
        r["#"] = i

    cols = ["#", "Published", "Title", "URL", "Category", "Main keyword", "All keywords", "Words",
            "Read min", "Sources", "Status", "Slug"]
    traffic_cols = ["Impressions (GSC)", "Clicks (GSC)", "CTR", "Avg position", "Ad-ready?", "Notes"]

    DATA.mkdir(exist_ok=True)
    with open(DATA / "articles-registry.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)

    wb = Workbook()
    ws = wb.active
    ws.title = "Articles"
    head = cols + traffic_cols
    ws.append(head)
    hdr_fill = PatternFill("solid", fgColor="1F6F5C")
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = hdr_fill
        c.alignment = Alignment(vertical="center", wrap_text=True)
    for r_i, r in enumerate(rows, start=2):
        ws.append([r[c] for c in cols] + [None, None, None, None, None, None])
        url_cell = ws.cell(row=r_i, column=cols.index("URL") + 1)
        url_cell.hyperlink = r["URL"]
        url_cell.font = Font(color="1F6F5C", underline="single")
        imp = f"{get_column_letter(len(cols) + 1)}{r_i}"
        clk = f"{get_column_letter(len(cols) + 2)}{r_i}"
        ctr = ws.cell(row=r_i, column=len(cols) + 3, value=f'=IF(N({imp})=0,"",{clk}/{imp})')
        ctr.number_format = "0.0%"
        ws.cell(row=r_i, column=len(cols) + 5, value=f'=IF(N({clk})>=50,"Yes","Not yet")')
    widths = [5, 12, 52, 58, 22, 30, 50, 8, 9, 9, 11, 40, 14, 12, 8, 12, 10, 30]
    for i, wdt in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = wdt
    ws.freeze_panes = "D2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(head))}{len(rows) + 1}"

    s = wb.create_sheet("Summary")
    n = len(rows) + 1
    s.append(["Metric", "Value"])
    for c in s[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = hdr_fill
    s.append(["Total articles", f"=COUNTA(Articles!C2:C{n})"])
    s.append(["Total words", f"=SUM(Articles!H2:H{n})"])
    s.append(["Avg words / article", f"=IFERROR(ROUND(AVERAGE(Articles!H2:H{n}),0),0)"])
    s.append(["Total impressions (GSC)", f"=SUM(Articles!M2:M{n})"])
    s.append(["Total clicks (GSC)", f"=SUM(Articles!N2:N{n})"])
    s.append(["Overall CTR", f'=IF(B5=0,"",B6/B5)'])
    s["B7"].number_format = "0.0%"
    s.append(["Ready for AdSense (rule of thumb: 30+ articles)", '=IF(B2>=30,"Yes - apply","Not yet")'])
    s.append([])
    s.append(["Articles by category", ""])
    s[f"A{s.max_row}"].font = Font(bold=True)
    for name in CATEGORIES.values():
        s.append([name, f'=COUNTIF(Articles!E2:E{n},"{name}")'])
    s.column_dimensions["A"].width = 48
    s.column_dimensions["B"].width = 18

    wb.save(DATA / "articles-registry.xlsx")
    print(f"Registry updated: {len(rows)} articles -> data/articles-registry.xlsx")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    c = sys.argv[1]
    if c == "check":
        sys.exit(cmd_check([Path(a) for a in sys.argv[2:]]))
    if c == "check-all":
        sys.exit(cmd_check(all_articles()))
    if c == "registry":
        cmd_registry(); sys.exit(0)
    print(__doc__); sys.exit(2)
