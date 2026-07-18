#!/usr/bin/env python3
"""營業稅銷售額按行業別 — the free read on industry revenue that includes SMEs.

The old source (web02.mof.gov.tw sys=220 report engine) served a single
3-digit-industry × 22-county × month cube, but its backend has been hanging
since at least 2026-07 (the host is up; sys=210/220 specifically time out on
every query, even a shrunk one — see references/endpoints.md). This script
now reads the 財政統計月報 static Excel on a *different*, healthy host,
service.mof.gov.tw, which splits that cube into two projections:

  表3-9  (23090) — 3-digit industry × month, NATIONAL     -> --industry / --list
  表3-11 (23110) — major-category × 22 counties × month    -> --county

The one thing neither projection gives is 3-digit × county in the same cell —
that lived only in the dead sys=220. Use national 3-digit or county
major-category and say which.

  python3 scripts/mof_industry.py --list 出版          # find the 3-digit name
  python3 scripts/mof_industry.py --industry 581       # national monthly series
  python3 scripts/mof_industry.py --industry 出版      # substring match on names
  python3 scripts/mof_industry.py --industry 581 --history 12   # 12-month series
  python3 scripts/mof_industry.py --county 批發        # a major-category by county
  python3 scripts/mof_industry.py --industry 581 --json

Caveats that matter:
- Unit is 新臺幣百萬元 (the old千元 source was 1000× finer text; numbers here are
  100× a 億元). 口徑 is 營業稅銷售額 self-reported by 稅籍行業別, not survey output.
- 營業稅法第 8 條 exempts magazines' own-publication sales and ad revenue, so
  58x publishing is structurally UNDERSTATED. State this when citing.
- VAT is filed bimonthly: a given month's row can be small; the 月報 lists the
  last 6 months, so read the trend, not one month.
- Coverage is 112 年 (2023) onward, where the source is .xlsx. 107-111 exist only
  as legacy .xls/.ods (not read here) or in the dead sys=220.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys

from twdata._fetch import FetchError, fetch
from twdata._xlsx import read_xlsx

BASE = "https://service.mof.gov.tw/public/Data/statistic/monthly/{ym}/{tbl}_{ym}.xlsx"
T_INDUSTRY = "23090"   # 表3-9  3-digit industry × month, national
T_COUNTY = "23110"     # 表3-11 major-category × 22 counties × month

_MONTH_RE = re.compile(r"(\d+)\s*年\s*(\d+)\s*月")


def _prev_ym(ym: int) -> int:
    """民國 YYYMM minus one month."""
    y, m = divmod(ym, 100)
    return (y - 1) * 100 + 12 if m == 1 else ym - 1


def _fetch_report(ym: int, tbl: str) -> bytes:
    return fetch(BASE.format(ym=ym, tbl=tbl), min_bytes=8_000)


def _latest_ym(tbl: str) -> int:
    """月報 lags 1-2 months; walk back from this month until a file resolves."""
    today = datetime.date.today()
    ym = (today.year - 1911) * 100 + today.month
    for _ in range(6):
        try:
            _fetch_report(ym, tbl)
            return ym
        except FetchError:
            ym = _prev_ym(ym)
    raise SystemExit("service.mof.gov.tw 最近 6 個月的月報都抓不到 — 稍後重試。")


def _norm_month(label: str) -> str:
    """'115年 2月' -> '2026-02'; anything unparseable passes through."""
    m = _MONTH_RE.search(label or "")
    if not m:
        return (label or "").strip()
    return f"{int(m.group(1)) + 1911}-{int(m.group(2)):02d}"


def _num(cell: str) -> float | None:
    v = (cell or "").strip().replace(",", "")
    if v in ("", "-", "－", "…", "(D)", "X"):
        return None
    try:
        return float(v)
    except ValueError:
        return None


# --- 表3-9 : 3-digit industry × month, national ----------------------------

def _parse_industry(body: bytes) -> dict:
    """-> {months: [6 AD months], industries: {code: {name, sales:[6]}}}.

    Columns (0-based): 0 大類 / 1 中類 / 2 小類(3-digit) / 3 名稱 / 4 家數 /
    5-10 sales for the last 6 months / 11 cumulative. Month labels live in the
    5th grid row (index 4), cols 5-10. All 7 worksheets share that header; the
    3-digit rows are spread across them.
    """
    sheets = read_xlsx(body)
    first = next(iter(sheets.values()))
    label_row = first[4] if len(first) > 4 else []
    months = [_norm_month(label_row[i]) if i < len(label_row) else f"col{i}"
              for i in range(5, 11)]
    industries: dict[str, dict] = {}
    for grid in sheets.values():
        for r in grid:
            if len(r) < 11:
                continue
            code = r[2].strip()
            if not (code.isdigit() and len(code) == 3):
                continue
            industries[code] = {
                "code": code,
                "name": r[3].strip(),
                "sales": [_num(r[i]) for i in range(5, 11)],
            }
    return {"months": months, "industries": industries}


def _match_industry(parsed: dict, keyword: str) -> list[str]:
    """Digit keyword = exact 3-digit code; text = substring on name."""
    inds = parsed["industries"]
    if keyword.isdigit():
        hits = [c for c in inds if c == keyword]
    else:
        hits = [c for c, d in inds.items() if keyword in d["name"]]
    if not hits:
        raise SystemExit(f"找不到行業 {keyword!r}。用 --list {keyword!r} 或 --list 看全部。")
    return hits


def _extend_series(code: str, latest_ym: int, months: int) -> list[tuple[str, float | None]]:
    """Walk back through monthly reports, taking each report's newest month,
    until `months` distinct months are collected."""
    seen: dict[str, float | None] = {}
    ym = latest_ym
    guard = 0
    while len(seen) < months and guard < months + 6:
        guard += 1
        try:
            parsed = _parse_industry(_fetch_report(ym, T_INDUSTRY))
        except FetchError:
            ym = _prev_ym(ym)
            continue
        ind = parsed["industries"].get(code)
        if ind:
            for mlabel, val in zip(parsed["months"], ind["sales"]):
                seen.setdefault(mlabel, val)
        ym = _prev_ym(ym)
    return sorted(seen.items())[-months:]


def _fmt(v: float | None) -> str:
    return "—" if v is None else f"{v / 100:,.2f}"  # 百萬元 -> 億元


def cmd_list(keyword: str | None) -> None:
    ym = _latest_ym(T_INDUSTRY)
    parsed = _parse_industry(_fetch_report(ym, T_INDUSTRY))
    hits = [(c, d["name"]) for c, d in parsed["industries"].items()
            if not keyword or keyword in d["name"] or keyword == c]
    for code, name in hits:
        print(f"  {code}  {name}")
    print(f"\n  {len(hits)} 個 3 碼行業 (民國 {ym // 100} 年 {ym % 100} 月 月報, 表3-9)")


def cmd_industry(keyword: str, history: int, as_json: bool) -> None:
    ym = _latest_ym(T_INDUSTRY)
    parsed = _parse_industry(_fetch_report(ym, T_INDUSTRY))
    hits = _match_industry(parsed, keyword)

    out = {"unit": "百萬元", "source": "MOF 財政統計月報 表3-9 營業稅銷售額 (含未上市/SME)",
           "granularity": "3碼行業 × 月, 全國", "industries": {}}
    for code in hits:
        name = parsed["industries"][code]["name"]
        series = _extend_series(code, ym, max(history, 6))
        out["industries"][code] = {"name": name,
                                    "series": [{"month": m, "sales": v} for m, v in series]}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    for code, d in out["industries"].items():
        print(f"{code} {d['name']}  — 營業稅銷售額, 全國 (億元)")
        for row in d["series"]:
            print(f"  {row['month']:<10}{_fmt(row['sales']):>14}")
        print()
    print("  口徑: 營業稅銷售額, 稅籍行業別自行申報, 含中小企業。單位百萬元, 顯示為億元。")
    print("  注意: 營業稅法第8條 — 雜誌自售出版品與廣告收入免稅, 58x 出版業結構性低估。")
    print("        雙月申報, 單月值偏小 — 讀趨勢而非單月。3碼×縣市 需舊 sys=220 (已故障)。")


# --- 表3-11 : major-category × 22 counties × month -------------------------

def _parse_county(body: bytes) -> dict:
    """-> {month, categories: [names], counties: {name: {cat: value}}}.

    Row layout: a header row starting with 地區別 lists the major categories
    (col 1 = 總計, col 2.. = categories); 總計 and each county follow.
    """
    def _squash(s: str) -> str:
        return (s or "").replace("　", "").replace("\n", "").replace(" ", "").strip()

    sheets = read_xlsx(body)
    grid = next(iter(sheets.values()))
    hdr_i = next((i for i, r in enumerate(grid)
                  if r and _squash(r[0]) == "地區別"), None)
    if hdr_i is None:
        raise FetchError("表3-11: 找不到地區別表頭列")
    hdr = grid[hdr_i]
    cats = [_squash(c) for c in hdr[1:]]
    month = ""
    for r in grid[:hdr_i]:
        for c in r:
            if _MONTH_RE.search(c or ""):
                month = _norm_month(c)
                break
        if month:
            break
    counties: dict[str, dict] = {}
    for r in grid[hdr_i + 1:]:
        if not r or not r[0].strip():
            continue
        cname = r[0].strip().replace("　", "")
        vals = {cats[j]: _num(r[j + 1]) for j in range(len(cats)) if j + 1 < len(r)}
        if any(v is not None for v in vals.values()):
            counties[cname] = vals
    return {"month": month, "categories": cats, "counties": counties}


def cmd_county(keyword: str | None, as_json: bool) -> None:
    ym = _latest_ym(T_COUNTY)
    parsed = _parse_county(_fetch_report(ym, T_COUNTY))
    cats = parsed["categories"]
    if keyword:
        matches = [c for c in cats if keyword in c or keyword == c]
        if not matches:
            raise SystemExit(f"找不到大類 {keyword!r}。可用: {'、'.join(c for c in cats if c)}")
        cat = matches[0]
    else:
        cat = cats[0]  # 總計

    rows = sorted(
        ((cty, v[cat]) for cty, v in parsed["counties"].items()
         if cty != "總計" and v.get(cat) is not None),
        key=lambda x: -x[1],
    )
    out = {"unit": "百萬元", "source": "MOF 財政統計月報 表3-11 營業稅銷售額 × 縣市",
           "month": parsed["month"], "category": cat,
           "counties": [{"county": c, "sales": v} for c, v in rows]}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"{cat} — 各縣市營業稅銷售額 ({parsed['month']}, 億元)")
    for c, v in rows:
        print(f"  {c:<8}{_fmt(v):>12}")
    print(f"\n  {len(rows)} 縣市。單位百萬元顯示為億元。大類 × 縣市 (非 3 碼)。")
    print(f"  可用大類: {'、'.join(c for c in cats if c and c != '總計')}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--industry", metavar="碼或名稱", help="表3-9: 數字=3碼精確, 文字=名稱子串, 全國月序列")
    g.add_argument("--county", nargs="?", const="", metavar="大類", help="表3-11: 一個大類的各縣市分布")
    g.add_argument("--list", nargs="?", const="", metavar="關鍵字", help="列出 3 碼行業名稱")
    ap.add_argument("--history", type=int, default=6, metavar="N", help="回溯 N 個月 (default 6)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.list is not None:
        cmd_list(a.list or None)
    elif a.county is not None:
        cmd_county(a.county or None, a.json)
    else:
        cmd_industry(a.industry, a.history, a.json)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except FetchError as e:
        print(f"FetchError: {e}", file=sys.stderr)
        sys.exit(1)
