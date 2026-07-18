#!/usr/bin/env python3
"""年齡結構 — the demographic axis of consumer demand, by county.

Age structure decides which categories a place buys (silver vs young-family vs
single-professional). NDC dataset 6327 carries three-band age shares and the
dependency ratio by county, ready-made — no need to aggregate the 2M-row village
file (ODRP052).

  python3 scripts/population.py --county          # 各縣市 三段年齡/老化指數/扶養比, ranked
  python3 scripts/population.py --county --year 2023
  python3 scripts/population.py --county --json

Ranks by 老化指數 (65+ ÷ 0-14 × 100) — high = ageing. Pairs with income_tax.py /
education.py (county roll-up) to add the demographic dimension to purchasing-power
tiering. Village/district-level age needs ODRP052 (2M rows) — not read here; this
is the county cut that answers most category questions.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys

from twdata._fetch import FetchError, fetch, decode, resolve_dataset

DATASET = 6327  # NDC 1-2 土地面積/戶數/人口/密度/年齡結構/扶養比 按主要都市分


def _col(row: dict, name: str):
    for k, v in row.items():
        if k and k.lstrip("﻿") == name:
            return v
    return None


def _f(v) -> float | None:
    s = (v or "").strip().replace(",", "")
    try:
        return float(s)
    except (ValueError, AttributeError):
        return None


def _load() -> list[dict]:
    meta = resolve_dataset(DATASET)
    url = next((d["url"] for d in meta["distribution"] if d["format"] == "CSV"), None)
    if not url:
        raise FetchError(f"dataset {DATASET}: no CSV distribution")
    body = fetch(url, freeze=True)   # annual, closed years — permanent
    return list(csv.DictReader(io.StringIO(decode(body))))


def cmd_county(year: int | None, as_json: bool) -> None:
    rows = _load()
    years = sorted({int(y) for r in rows if (y := _f(_col(r, "年")))})
    if not years:
        raise SystemExit("dataset 6327: 讀不到年份欄。")
    year = year or years[-1]
    if year not in years:
        raise SystemExit(f"年份 {year} 不在資料內。可用: {years}")

    recs = []
    for r in rows:
        if _f(_col(r, "年")) != year:
            continue
        area = (_col(r, "地區") or "").strip()
        if not area or "合計" in area:
            continue
        young = _f(_col(r, "0~14歲百分比"))
        working = _f(_col(r, "15~64歲百分比"))
        old = _f(_col(r, "65歲以上百分比"))
        dep = _f(_col(r, "扶養百分比"))
        ageing = (old / young * 100) if young and old else None
        recs.append({"county": area, "young_0_14": young, "working_15_64": working,
                     "old_65up": old, "dependency_ratio": dep, "ageing_index": ageing,
                     "population": _f(_col(r, "年底人口數"))})
    recs.sort(key=lambda r: -(r["ageing_index"] or 0))
    if as_json:
        print(json.dumps({"year": year, "source": "NDC 6327", "counties": recs},
                         ensure_ascii=False, indent=2))
        return
    print(f"各地區年齡結構 ({year}年, NDC 6327; 含六都與指標鄉鎮市)")
    print(f"  {'地區':<10}{'0-14%':>8}{'15-64%':>9}{'65+%':>8}{'老化指數':>10}{'扶養比':>8}")
    for r in recs:
        def p(x): return f"{x:.1f}" if x is not None else "—"
        print(f"  {r['county'][:10]:<10}{p(r['young_0_14']):>8}{p(r['working_15_64']):>9}"
              f"{p(r['old_65up']):>8}{p(r['ageing_index']):>10}{p(r['dependency_ratio']):>8}")
    print("\n  老化指數=65+/0-14×100 (高=老化); 扶養比=(0-14+65+)/15-64。按老化指數排序。")
    print("  年輕縣市=年輕家庭/首購/教養消費; 老化縣市=醫療保健/銀髮。可與所得/教育縣市層交叉。")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--county", action="store_true", required=True,
                    help="各縣市三段年齡結構、老化指數、扶養比")
    ap.add_argument("--year", type=int, metavar="AD", help="西元年 (預設最新)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    cmd_county(a.year, a.json)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except FetchError as e:
        print(f"FetchError: {e}", file=sys.stderr)
        sys.exit(1)
