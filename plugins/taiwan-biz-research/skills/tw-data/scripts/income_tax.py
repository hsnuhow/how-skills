#!/usr/bin/env python3
"""綜合所得稅申報統計 — every filing household, not a survey sample.

The 財政部財政資訊中心 (FIA) publishes 綜稅 statistics from the whole filing
population by county, bracket and quantile — a fuller picture of who has how much
than the 家庭收支調查 sample, and the backbone of purchasing-power tiering. Three
reads:

  --county               所得應納稅額及稅率 by county: households, total income,
                         per-household income, effective tax rate (表6A-1, 加計股利)
  --structure [縣市]     各類所得 by county: salary vs dividend vs business —
                         the income-composition that drives spending propensity (表16-1)
  --village 縣市         村里-level income: mean/median per household, the finest
                         geographic income map in Taiwan (表165-9)

  python3 scripts/income_tax.py --county
  python3 scripts/income_tax.py --structure          # salary/dividend share, all counties
  python3 scripts/income_tax.py --structure 臺北市    # full composition for one county
  python3 scripts/income_tax.py --village 新竹市 --json
  python3 scripts/income_tax.py --county --year 111

Caveats:
- Amounts are 千元 (NT$ thousands). Per-household shown as 萬元/戶.
- 加計分開計稅之股利所得: since 107年 dividends can be taxed separately; 表6A-1 folds
  them back in for a consistent total. Pre-107 needs the old 表6-1 (not read here).
- The filing unit is a tax household (納稅單位), not a person or a 家庭收支 household.
- Statistics lag ~3 years (income year → filing → publication).
"""

from __future__ import annotations

import argparse
import csv
import datetime
import io
import json
import sys

from twdata._fetch import FetchError, fetch, decode

BASE = "https://www.fia.gov.tw/WEB/fia/ias/ias{y}/{y}_{tbl}.csv"
T_COUNTY = "6A-1"      # 各縣市 稅率 (加計股利), 107年→
T_STRUCTURE = "16-1"   # 各縣市 各類所得, 101年→
T_VILLAGE = "165-9"    # 村里 所得總額, 101年→


def _fetch_year(tbl: str, year: int, *, probe: bool = False) -> list[dict]:
    """A closed tax year never changes → freeze. Probing for the latest year must
    bypass the cache to see a newly published file."""
    body = fetch(BASE.format(y=year, tbl=tbl), min_bytes=200,
                 use_cache=not probe, freeze=not probe)
    return list(csv.DictReader(io.StringIO(decode(body))))


def _latest_year(tbl: str) -> int:
    """Walk back from this ROC year until a file resolves (stats lag ~3y)."""
    roc = datetime.date.today().year - 1911
    for year in range(roc, roc - 8, -1):
        try:
            _fetch_year(tbl, year, probe=True)
            return year
        except FetchError:
            continue
    raise SystemExit(f"表{tbl}: 最近 8 個年度都抓不到 — 稍後重試或確認表號。")


def _num(v: str | None) -> float | None:
    s = (v or "").strip().replace(",", "")
    if s in ("", "-", "－", "…", "X"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _col(row: dict, *names: str):
    """First matching column (headers carry a BOM on the first key and vary)."""
    for n in names:
        for k, v in row.items():
            if k and k.lstrip("﻿") == n:
                return v
    return None


def _norm(s: str) -> str:
    return s.replace("台", "臺").strip()


def _is_total(name: str) -> bool:
    return name.strip() in ("合計", "總計", "全國")


def _money(v: float | None) -> str:      # 千元 -> 億元
    return "—" if v is None else f"{v / 1e5:,.1f}"


def _per_hh(total: float | None, hh: float | None) -> str:   # 千元/戶 -> 萬元/戶
    if not total or not hh:
        return "—"
    return f"{total / hh / 10:,.1f}"


def cmd_county(year: int | None, as_json: bool) -> None:
    year = year or _latest_year(T_COUNTY)
    rows = _fetch_year(T_COUNTY, year)
    out = {"unit": "千元", "year_roc": year, "table": "表6A-1 (加計股利)",
           "source": "MOF FIA 綜稅所得應納稅額及稅率各縣市", "counties": []}
    for r in rows:
        name = (_col(r, "縣市別") or "").strip()
        if not name or _is_total(name):
            continue
        hh = _num(_col(r, "納稅單位"))
        total = _num(_col(r, "綜合所得總額(加計分開計稅之股利所得)", "綜合所得總額"))
        eff = _num(_col(r, "有效稅率"))
        avg = _num(_col(r, "平均稅率"))
        out["counties"].append({"county": name, "households": hh, "total_income": total,
                                "per_household": (total / hh if total and hh else None),
                                "effective_tax_rate": eff, "average_tax_rate": avg})
    out["counties"].sort(key=lambda c: -(c["per_household"] or 0))
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"綜稅各縣市所得與稅率 ({year}年, 表6A-1 加計股利)")
    print(f"  {'縣市':<8}{'戶數':>10}{'綜所總額(億)':>14}{'人均(萬/戶)':>12}{'有效稅率%':>10}")
    for c in out["counties"]:
        hh = f"{c['households']:,.0f}" if c["households"] else "—"
        eff = f"{c['effective_tax_rate']:.2f}" if c["effective_tax_rate"] is not None else "—"
        print(f"  {c['county']:<8}{hh:>10}{_money(c['total_income']):>14}"
              f"{_per_hh(c['total_income'], c['households']):>12}{eff:>10}")
    print("\n  人均=綜所總額/戶。有效稅率=稅負/綜所總額, 反映所得水準。全體申報戶(非抽樣)。")


def cmd_structure(county: str | None, year: int | None, as_json: bool) -> None:
    year = year or _latest_year(T_STRUCTURE)
    rows = _fetch_year(T_STRUCTURE, year)
    recs = []
    for r in rows:
        name = (_col(r, "縣市別") or "").strip()
        if not name or _is_total(name):
            continue
        total = _num(_col(r, "合計"))
        salary = _num(_col(r, "薪資所得"))
        dividend = _num(_col(r, "股利所得"))
        business = _num(_col(r, "營利所得"))
        rec = {"county": name, "total": total, "salary": salary, "dividend": dividend,
               "business": business,
               "salary_share": (salary / total * 100 if salary and total else None),
               "dividend_share": (dividend / total * 100 if dividend and total else None)}
        recs.append(rec)

    if county:
        cn = _norm(county)
        match = next((r for r in recs if _norm(r["county"]) == cn
                      or cn in _norm(r["county"])), None)
        if not match:
            raise SystemExit(f"找不到縣市 {county!r}。可用: {'、'.join(r['county'] for r in recs)}")
        row = next(r for r in rows if (_col(r, "縣市別") or "").strip() == match["county"])
        cats = ["營利所得", "執行業務所得", "薪資所得", "利息所得", "租賃及權利金",
                "財產交易所得", "股利所得", "退職所得", "其他所得"]
        total = match["total"]
        detail = [{"category": c, "amount": _num(_col(row, c)),
                   "share": (_num(_col(row, c)) / total * 100
                             if _num(_col(row, c)) and total else None)} for c in cats]
        out = {"unit": "千元", "year_roc": year, "county": match["county"],
               "total_income": total, "composition": detail}
        if as_json:
            print(json.dumps(out, ensure_ascii=False, indent=2)); return
        print(f"{match['county']} 各類所得結構 ({year}年, 表16-1)  合計 {_money(total)} 億")
        for d in sorted(detail, key=lambda x: -(x["amount"] or 0)):
            sh = f"{d['share']:.1f}%" if d["share"] is not None else "—"
            print(f"  {d['category']:<12}{_money(d['amount']):>12} 億{sh:>9}")
        return

    recs.sort(key=lambda r: -(r["dividend_share"] or 0))
    if as_json:
        print(json.dumps({"unit": "千元", "year_roc": year, "counties": recs},
                         ensure_ascii=False, indent=2)); return
    print(f"各縣市所得結構: 薪資型 vs 資本型 ({year}年, 表16-1)")
    print(f"  {'縣市':<8}{'薪資占比%':>10}{'股利占比%':>10}")
    for r in recs:
        s = f"{r['salary_share']:.1f}" if r["salary_share"] is not None else "—"
        d = f"{r['dividend_share']:.1f}" if r["dividend_share"] is not None else "—"
        print(f"  {r['county']:<8}{s:>10}{d:>10}")
    print("\n  股利占比高=資本型所得(高所得, 消費傾向低); 薪資占比高=受薪型。按股利占比排序。")


def cmd_village(county: str, year: int | None, top: int, as_json: bool) -> None:
    year = year or _latest_year(T_VILLAGE)
    rows = _fetch_year(T_VILLAGE, year)
    cn = _norm(county)
    vills = []
    for r in rows:
        area = _norm((_col(r, "縣市別") or "").strip())   # e.g. 臺北市松山區
        village = (_col(r, "村里") or "").strip()
        if village in ("合計", "總計", "其他"):   # rollup / unlocatable rows
            continue
        if not area.startswith(cn) and cn not in area:
            continue
        vills.append({"area": area, "village": village,
                      "households": _num(_col(r, "納稅單位(戶)", "納稅單位")),
                      "mean": _num(_col(r, "平均數")), "median": _num(_col(r, "中位數"))})
    if not vills:
        raise SystemExit(f"找不到縣市 {county!r} 的村里資料 (縣市名需為全稱, 如 臺北市/新竹市)。")
    vills.sort(key=lambda v: -(v["median"] or 0))
    out = {"unit": "千元", "year_roc": year, "county": _norm(county),
           "village_count": len(vills), "table": "表165-9",
           "villages": vills if as_json else vills[:top]}
    if as_json:
        print(json.dumps(out, ensure_ascii=False, indent=2)); return
    meds = sorted(v["median"] for v in vills if v["median"] is not None)
    cmed = meds[len(meds) // 2] if meds else None
    print(f"{_norm(county)} 村里所得 ({year}年, 表165-9): {len(vills)} 村里, "
          f"中位數的中位數 {cmed/10:.1f} 萬/戶" if cmed else "")
    print(f"  {'區/里':<20}{'戶數':>8}{'平均(萬/戶)':>12}{'中位(萬/戶)':>12}")
    for v in vills[:top]:
        hh = f"{v['households']:,.0f}" if v["households"] else "—"
        mean = f"{v['mean']/10:,.1f}" if v["mean"] is not None else "—"
        med = f"{v['median']/10:,.1f}" if v["median"] is not None else "—"
        print(f"  {(v['area']+v['village'])[:20]:<20}{hh:>8}{mean:>12}{med:>12}")
    print(f"\n  按中位數排序, 顯示前 {top}。平均>>中位=右偏(少數高所得拉高)。單位萬元/戶。")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--county", action="store_true", help="各縣市所得與有效稅率 (表6A-1)")
    g.add_argument("--structure", nargs="?", const="", metavar="縣市",
                   help="各類所得結構; 給縣市看單一, 不給看全部薪資/股利占比 (表16-1)")
    g.add_argument("--village", metavar="縣市", help="村里級所得, 縣市全稱 (表165-9)")
    ap.add_argument("--year", type=int, metavar="ROC", help="民國年度 (預設最新)")
    ap.add_argument("--top", type=int, default=20, metavar="N", help="--village 顯示前 N (default 20)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.county:
        cmd_county(a.year, a.json)
    elif a.village is not None:
        cmd_village(a.village, a.year, a.top, a.json)
    else:
        cmd_structure(a.structure or None, a.year, a.json)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except FetchError as e:
        print(f"FetchError: {e}", file=sys.stderr)
        sys.exit(1)
