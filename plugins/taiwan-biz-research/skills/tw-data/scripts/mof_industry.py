#!/usr/bin/env python3
"""營業稅銷售額按行業別 — the only free read on industry revenue that includes SMEs.

MOF 財政統計資料庫, monthly, by 22 counties, down to 3-digit 稅務行業小類
(e.g. 581 新聞、雜誌、期刊、書籍及其他出版業). This is the complement to TWSE's
listed-only view: when an industry's players are unlisted (media, education,
services), this is the one series that still sees them.

  python3 scripts/mof_industry.py --list 出版          # find the industry name
  python3 scripts/mof_industry.py --industry 581       # national sales, by period
  python3 scripts/mof_industry.py --industry 出版      # substring match on names
  python3 scripts/mof_industry.py --industry 581 --history 5   # annual series
  python3 scripts/mof_industry.py --industry 581 --county      # county breakdown
  python3 scripts/mof_industry.py --industry 581 --json

Caveats that matter:
- 口徑 is 營業稅銷售額 as *self-reported* by 稅籍行業別 — not survey output.
- 營業稅法第 8 條 exempts magazines' own-publication sales and their ad revenue,
  so 58x publishing numbers are structurally UNDERSTATED. State this when citing.
- VAT is filed bimonthly: odd-month values are tiny. Use annual or cumulative.
- 112 年 switched to the 9th revision of the 稅務行業分類 (funid i0520); 107-111
  use the 8th (i0509). Names differ across the seam — joins need a mapping.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
import time

from twdata._fetch import FetchError, fetch, read_csv_rows

# funid pins a classification revision to a year range; codspc0 is the row count
# the export form expects for that revision. Wrong pairings silently return the
# newest year the funid knows — see _guard_year().
FUNIDS = [  # (funid, roc_from, roc_to, codspc0)
    ("i0520", 112, 116, "0,358,"),
    ("i0509", 107, 111, "0,356,"),
]

URL = ("https://web02.mof.gov.tw/njswww/webMain.aspx?sys=220&ym={y}00&ymt={y}12"
       "&kind=21&type=6&funid={funid}&cycle=41&outmode=12&compmode=00&outkind=3"
       "&fldspc=23,23,&codspc0={codspc0}&utf=1")

_CODE = re.compile(r"^([A-Z]\.|\d+)")


def _funid_for(year: int) -> tuple[str, str]:
    for funid, lo, hi, codspc0 in FUNIDS:
        if lo <= year <= hi:
            return funid, codspc0
    raise SystemExit(f"民國 {year} 年不在已知 funid 範圍 (107-116)。新年度需要查新的 funid。")


def _fetch_year(year: int) -> bytes:
    """web02 drops connections now and then; one retry is usually enough."""
    funid, codspc0 = _funid_for(year)
    url = URL.format(y=year, funid=funid, codspc0=codspc0)
    for attempt in (1, 2):
        try:
            return fetch(url, min_bytes=50_000)
        except FetchError:
            if attempt == 2:
                raise
            time.sleep(2)
    raise AssertionError  # unreachable


def _parse(body: bytes) -> dict:
    """-> {header: [...counties], rows: [(period, industry, [values])]}

    First column is a compound '{期間}/ {行業}'. Values: (D) = 保密隱匿,
    － = none, negatives are real (銷售折讓). Unit is 千元 throughout.
    """
    raw = read_csv_rows(body)
    header = [h.split("/")[0] for h in raw[0][1:]]
    rows = []
    for r in raw[1:]:
        if not r or "/" not in r[0]:
            continue
        period, industry = (p.strip() for p in r[0].split("/", 1))
        vals = []
        for v in r[1:]:
            v = v.strip()
            if v in ("(D)", "－", "-", "…", ""):
                vals.append(None)
            else:
                try:
                    vals.append(int(v))
                except ValueError:
                    vals.append(None)
        rows.append((period, industry, vals))
    return {"header": header, "rows": rows}


def _guard_year(parsed: dict, year: int) -> None:
    """The silent-fallback trap: ask i0509 for 114 and you get 111's file back,
    HTTP 200, bytes identical to the real 111 file. The ym parameter cannot be
    trusted — only the periods inside the body can."""
    want = f"{year}年"
    if not any(p.startswith(want) for p, _, _ in parsed["rows"]):
        have = sorted({p.split(" ")[0] for p, _, _ in parsed["rows"]})
        raise FetchError(
            f"asked for 民國 {year} 年 but the file contains {have} — "
            "web02 silently falls back to the newest year its funid covers; "
            "the requested year is probably not published yet"
        )


def _match(parsed: dict, keyword: str) -> list[str]:
    """Digit keywords match the 行業 code exactly; text matches the name as a
    substring. Never sum matches — the file holds aggregates and their
    sub-industries in one column (58 contains 581 and 582)."""
    names = []
    for _, industry, _ in parsed["rows"]:
        if industry not in names:
            names.append(industry)
    if keyword.isdigit():
        hits = [n for n in names if (_CODE.match(n) or [""])[0].rstrip(".") == keyword]
    else:
        hits = [n for n in names if keyword in n]
    if not hits:
        raise SystemExit(f"找不到行業 {keyword!r}。用 --list {keyword!r} 或 --list 看全部。")
    return hits


def _latest_year() -> int:
    roc = datetime.date.today().year - 1911
    for y in (roc, roc - 1):
        try:
            parsed = _parse(_fetch_year(y))
            _guard_year(parsed, y)
            return y
        except FetchError:
            continue
    raise SystemExit("最近兩個年度都抓不到 — web02 可能整站故障，稍後重試。")


def _fmt(v: int | None) -> str:
    return "—" if v is None else f"{v / 1e5:,.2f}"  # 千元 → 億元


def cmd_list(keyword: str | None) -> None:
    year = _latest_year()
    parsed = _parse(_fetch_year(year))
    seen = []
    for _, industry, _ in parsed["rows"]:
        if industry not in seen and (not keyword or keyword in industry):
            seen.append(industry)
    for n in seen:
        print(f"  {n}")
    print(f"\n  {len(seen)} 個行業 (民國 {year} 年檔, 稅務行業分類)")


def cmd_industry(keyword: str, history: int, county: bool, as_json: bool) -> None:
    year = _latest_year()
    parsed = _parse(_fetch_year(year))
    _guard_year(parsed, year)
    hits = _match(parsed, keyword)

    out = {"unit": "千元", "source": "MOF 財政統計資料庫 營業稅銷售額 (含未上市/SME)",
           "industries": {}}

    for name in hits:
        # annual rows ("114年") for closed years; the running year only has the
        # cumulative row ("115年 (1~4月)") — label it as such, never annualise.
        series = []
        for y in range(year, year - max(history, 1), -1):
            p = parsed if y == year else _parse(_fetch_year(y))
            if y != year:
                _guard_year(p, y)
            for period, industry, vals in p["rows"]:
                if industry == name and (period == f"{y}年" or period.startswith(f"{y}年 (")):
                    series.append({"period": period, "national": vals[0]})
        out["industries"][name] = {"series": series}

        if county:
            for period, industry, vals in reversed(parsed["rows"]):
                if industry == name and (period == f"{year}年" or period.startswith(f"{year}年 (")):
                    pairs = sorted(
                        (c, v) for c, v in zip(parsed["header"][1:], vals[1:]) if v is not None
                    )
                    pairs.sort(key=lambda x: -x[1])
                    out["industries"][name]["county"] = {"period": period, "values": pairs}
                    break

    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    for name, data in out["industries"].items():
        print(f"{name}  — 營業稅銷售額, 全國 (億元)")
        for row in data["series"]:
            print(f"  {row['period']:<14}{_fmt(row['national']):>14}")
        if "county" in data:
            c = data["county"]
            print(f"\n  縣市別 ({c['period']}, 億元):")
            for county_name, v in c["values"]:
                print(f"    {county_name:<8}{_fmt(v):>12}")
        print()
    print("  口徑: 營業稅銷售額, 稅籍行業別自行申報, 含中小企業。")
    print("  注意: 營業稅法第8條 — 雜誌自售出版品與廣告收入免稅, 58x 出版業數字結構性低估。")
    print("        (D)=保密隱匿。雙月申報, 單數月偏小 — 用年值或累計值。")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--industry", metavar="碼或名稱", help="數字=行業碼精確匹配, 文字=名稱子串")
    g.add_argument("--list", nargs="?", const="", metavar="關鍵字", help="列出行業名稱")
    ap.add_argument("--history", type=int, default=2, metavar="N", help="回溯 N 年 (default 2)")
    ap.add_argument("--county", action="store_true", help="最新期間的縣市別拆分")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.list is not None:
        cmd_list(a.list or None)
    else:
        cmd_industry(a.industry, a.history, a.county, a.json)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except FetchError as e:
        print(f"FetchError: {e}", file=sys.stderr)
        sys.exit(1)
