#!/usr/bin/env python3
"""上市公司月營收 — a free, monthly, company-level demand tracker.

Every TWSE-listed company must report monthly revenue by the 10th of the
following month. The feed carries 產業別 on each row, so rolling it up gives an
industry-level YoY series that is usually a paid product elsewhere. This is the
best free read on "what is actually selling in Taiwan right now".

Source: openapi.twse.com.tw/v1/opendata/t187ap05_L (上市), _P (公發). Keyless.

Caveat that shapes everything: **this is a current-month snapshot, not a
history.** The endpoint only ever serves the latest month. To build a series you
must poll monthly and accumulate — or backfill from MOPS (see
references/endpoints.md). Amounts are 千元 (thousands of NTD).

Usage:
    python3 twse_revenue.py                      # industry roll-up, by YoY
    python3 twse_revenue.py --top 15             # fastest-growing companies
    python3 twse_revenue.py --bottom 15          # sharpest decliners
    python3 twse_revenue.py --industry 半導體業    # companies within an industry
    python3 twse_revenue.py --company 2330
    python3 twse_revenue.py --json
"""

import argparse
import json
import sys
from collections import defaultdict

from twdata._fetch import decode, fetch, roc_to_ad

LISTED = "https://openapi.twse.com.tw/v1/opendata/t187ap05_L"
PUBLIC = "https://openapi.twse.com.tw/v1/opendata/t187ap05_P"

# The feed reports 千元; report 億元, which is how these figures get discussed.
THOUSANDS_TO_YI = 1e5


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def load(url=LISTED):
    rows = json.loads(decode(fetch(url)))
    if not rows:
        raise SystemExit("empty feed — TWSE publishes around the 10th; too early in the month?")
    out = []
    for r in rows:
        cur = _num(r.get("營業收入-當月營收"))
        prior = _num(r.get("營業收入-去年當月營收"))
        if cur is None:
            continue
        out.append({
            "code": r.get("公司代號"),
            "name": r.get("公司名稱"),
            "industry": (r.get("產業別") or "其他").strip(),
            "revenue": cur,
            "revenue_ly": prior,
            "yoy": _num(r.get("營業收入-去年同月增減(%)")),
            "mom": _num(r.get("營業收入-上月比較增減(%)")),
            "ytd": _num(r.get("累計營業收入-當月累計營收")),
            "ytd_yoy": _num(r.get("累計營業收入-前期比較增減(%)")),
        })
    period = roc_to_ad(rows[0].get("資料年月", ""))
    return period, out


def industry_rollup(rows):
    """Aggregate to industry. YoY is computed from summed revenue, not averaged
    from the per-company percentages — averaging those would weight a NT$50m
    company the same as TSMC."""
    agg = defaultdict(lambda: {"revenue": 0.0, "revenue_ly": 0.0, "n": 0})
    for r in rows:
        a = agg[r["industry"]]
        a["revenue"] += r["revenue"]
        a["n"] += 1
        if r["revenue_ly"]:
            a["revenue_ly"] += r["revenue_ly"]
    out = []
    for name, a in agg.items():
        yoy = ((a["revenue"] - a["revenue_ly"]) / a["revenue_ly"] * 100) if a["revenue_ly"] else None
        out.append({"industry": name, "revenue": a["revenue"], "yoy": yoy, "companies": a["n"]})
    return sorted(out, key=lambda x: (x["yoy"] is None, -(x["yoy"] or 0)))


def _fmt_yoy(v):
    return f"{v:+7.1f}%" if v is not None else "      —"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--top", type=int, metavar="N", help="fastest-growing companies by YoY")
    g.add_argument("--bottom", type=int, metavar="N", help="sharpest decliners by YoY")
    g.add_argument("--industry", metavar="名稱", help="companies within one industry")
    g.add_argument("--company", metavar="代號", help="one company by code")
    ap.add_argument("--min-revenue", type=float, default=1.0, metavar="億",
                    help="ignore companies below this monthly revenue (default 1億) — "
                         "tiny bases produce meaningless YoY spikes")
    ap.add_argument("--public", action="store_true", help="公發 instead of 上市")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    period, rows = load(PUBLIC if a.public else LISTED)
    ym = f"{period[:4]}-{period[4:]}" if len(period) >= 6 else period

    if a.company:
        hit = [r for r in rows if r["code"] == a.company]
        if not hit:
            raise SystemExit(f"找不到公司代號 {a.company}")
        r = hit[0]
        if a.json:
            print(json.dumps({"period": ym, **r}, ensure_ascii=False, indent=2)); return
        print(f"{r['name']} ({r['code']}) · {r['industry']} · {ym}")
        print(f"  當月營收   {r['revenue'] / THOUSANDS_TO_YI:12,.1f} 億")
        print(f"  去年同月   {(r['revenue_ly'] or 0) / THOUSANDS_TO_YI:12,.1f} 億")
        print(f"  YoY        {_fmt_yoy(r['yoy'])}      MoM {_fmt_yoy(r['mom'])}")
        print(f"  累計營收   {(r['ytd'] or 0) / THOUSANDS_TO_YI:12,.1f} 億   累計 YoY {_fmt_yoy(r['ytd_yoy'])}")
        return

    if a.top or a.bottom or a.industry:
        pool = [r for r in rows if r["revenue"] / THOUSANDS_TO_YI >= a.min_revenue and r["yoy"] is not None]
        if a.industry:
            pool = [r for r in pool if a.industry in r["industry"]]
            if not pool:
                inds = sorted({r["industry"] for r in rows})
                raise SystemExit(f"找不到產業 {a.industry!r}。可用:\n  " + "\n  ".join(inds))
            pool.sort(key=lambda r: -r["yoy"])
            title = f"{a.industry} · {ym}"
        else:
            pool.sort(key=lambda r: -r["yoy"] if a.top else r["yoy"])
            pool = pool[: (a.top or a.bottom)]
            title = f"{'成長最快' if a.top else '衰退最深'} · {ym}"

        if a.json:
            print(json.dumps({"period": ym, "companies": pool}, ensure_ascii=False, indent=2)); return
        print(f"{title}   (營收 ≥ {a.min_revenue} 億)")
        print(f"  {'公司':<12}{'產業':<14}{'當月營收(億)':>12}{'YoY':>9}")
        for r in pool:
            print(f"  {r['name'][:11]:<12}{r['industry'][:13]:<14}"
                  f"{r['revenue'] / THOUSANDS_TO_YI:>12,.1f}{_fmt_yoy(r['yoy']):>9}")
        return

    roll = industry_rollup(rows)
    if a.json:
        print(json.dumps({"period": ym, "industries": roll}, ensure_ascii=False, indent=2)); return

    total = sum(r["revenue"] for r in rows)
    total_ly = sum(r["revenue_ly"] or 0 for r in rows)
    print(f"上市公司月營收 · {ym} · {len(rows)} 家")
    print(f"  全體合計 {total / THOUSANDS_TO_YI:,.0f} 億   "
          f"YoY {_fmt_yoy((total - total_ly) / total_ly * 100 if total_ly else None)}\n")
    print(f"  {'產業別':<18}{'家數':>5}{'月營收(億)':>13}{'YoY':>9}")
    for r in roll:
        print(f"  {r['industry'][:17]:<18}{r['companies']:>5}"
              f"{r['revenue'] / THOUSANDS_TO_YI:>13,.0f}{_fmt_yoy(r['yoy']):>9}")
    print("\n  註: 僅上市公司，不含未上市與中小企業。單位由千元換算為億元。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
