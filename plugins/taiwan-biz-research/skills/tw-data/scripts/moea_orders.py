#!/usr/bin/env python3
"""外銷訂單、製造業生產、零售餐飲營業額 — MOEA's demand and output series.

外銷訂單 is Taiwan's most useful leading indicator: orders are booked before
they're produced and shipped, so this turns before industrial production and
before exports. It is also a component of the NDC leading index.

Source: service.moea.gov.tw/EE520/opendata/*.csv, keyless, UTF-8 BOM, ROC dates
packed as YYYMM (07301 = 1984-01). Note the MOEA HTML portal is Cloudflare-403
while these CSVs are not — a blocked portal doesn't mean blocked data.

零售/餐飲 is released on the 23rd-26th of the following month; 外銷訂單 around
the 20th.

Usage:
    python3 moea_orders.py --orders 電子           # 電子產品外銷訂單 + YoY
    python3 moea_orders.py --orders 資通訊
    python3 moea_orders.py --retail               # 批發零售餐飲營業額指數
    python3 moea_orders.py --production           # 製造業生產價值指數
    python3 moea_orders.py --production --sector 半導體
    python3 moea_orders.py --production --sectors  # list available 行業別
    python3 moea_orders.py --orders 電子 --history 24 --json
"""

import argparse
import json
import sys
from collections import defaultdict

from twdata._fetch import dataset_file, read_csv, roc_to_ad

ORDERS = {"電子": (16362, "電子產品"), "資通訊": (16361, "資通訊產品")}
PRODUCTION = 16366
RETAIL = 16365


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _series(dataset_id, value_col, period_col="資料期(民國年)", filter_col=None, filter_val=None):
    """MOEA ships long-format CSV: one row per category per period.

    The category filter is an exact match, and must stay that way. These files
    carry the aggregate and its sub-industries in the same column — '製造業'
    alongside '其他製造業', '食品製造業' and so on. A substring match silently
    collapses several industries into one series and yields a plausible-looking
    number that is wrong, with duplicate periods as the only visible symptom.
    """
    rows = read_csv(dataset_file(dataset_id, fmt="CSV"))
    out = []
    for r in rows:
        if filter_col and filter_val and (r.get(filter_col) or "").strip() != filter_val:
            continue
        v = _num(r.get(value_col))
        p = (r.get(period_col) or "").strip()
        if v is None or not p:
            continue
        out.append({"period": roc_to_ad(p), "value": v,
                    "unit": (r.get("計量單位") or "").strip(),
                    "category": (r.get(filter_col) or "").strip() if filter_col else None})
    out.sort(key=lambda x: x["period"])
    return out


def with_yoy(rows):
    """Attach YoY by looking up the same month a year earlier."""
    by_period = {r["period"]: r["value"] for r in rows}
    for r in rows:
        p = r["period"]
        prior = f"{int(p[:4]) - 1}{p[4:]}" if len(p) >= 6 else None
        base = by_period.get(prior)
        r["yoy"] = ((r["value"] - base) / base * 100) if base else None
    return rows


def show(title, rows, history, as_json):
    if not rows:
        raise SystemExit(f"{title}: no rows — the CSV layout may have changed")
    rows = with_yoy(rows)
    if as_json:
        print(json.dumps({"series": title, "rows": rows[-history:]}, ensure_ascii=False, indent=2))
        return
    latest = rows[-1]
    unit = latest.get("unit") or ""
    yoy = f"{latest['yoy']:+.1f}%" if latest["yoy"] is not None else "—"
    print(f"{title}  最新 {latest['period'][:4]}-{latest['period'][4:]}: "
          f"{latest['value']:,.2f} {unit}   YoY {yoy}")
    print(f"  資料範圍 {rows[0]['period']} → {rows[-1]['period']}  ({len(rows):,} 期)")
    print(f"\n  近 {history} 期:")
    for r in rows[-history:]:
        y = f"{r['yoy']:+7.1f}%" if r["yoy"] is not None else "      —"
        print(f"    {r['period'][:4]}-{r['period'][4:]}  {r['value']:>12,.2f}  {y}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--orders", metavar="類別", help=f"外銷訂單: {' / '.join(ORDERS)}")
    g.add_argument("--production", action="store_true", help="製造業生產價值指數")
    g.add_argument("--retail", action="store_true", help="批發零售及餐飲業營業額指數")
    ap.add_argument("--sector", metavar="行業", help="filter 製造業生產 to one 行業別")
    ap.add_argument("--sectors", action="store_true", help="list available 行業別")
    ap.add_argument("--history", type=int, default=12, metavar="N")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.orders:
        if a.orders not in ORDERS:
            raise SystemExit(f"未知類別 {a.orders!r}。可用: {' / '.join(ORDERS)}")
        ds, label = ORDERS[a.orders]
        show(f"外銷訂單 · {label}", _series(ds, "統計值(金額)"), a.history, a.json)

    elif a.retail:
        rows = read_csv(dataset_file(RETAIL, fmt="CSV"))
        cols = list(rows[0]) if rows else []
        vcol = next((c for c in cols if "統計值" in c), None)
        fcol = next((c for c in cols if "行業" in c and "代碼" not in c), None)
        if not vcol:
            raise SystemExit(f"找不到統計值欄位; 欄位為 {cols}")
        target = "零售業" if fcol else None
        show(f"營業額指數 · {target or '全體'}",
             _series(RETAIL, vcol, filter_col=fcol, filter_val=target), a.history, a.json)

    else:
        if a.sectors:
            rows = read_csv(dataset_file(PRODUCTION, fmt="CSV"))
            seen = sorted({(r.get("行業別") or "").strip() for r in rows if r.get("行業別")})
            for s in seen:
                print(" ", s)
            return
        sector = a.sector or "製造業"
        rows = _series(PRODUCTION, "統計值(指數)", filter_col="行業別", filter_val=sector)
        if not rows:
            raise SystemExit(f"找不到行業 {sector!r} — 用 --sectors 看可用清單")
        show(f"製造業生產價值指數 · {sector}", rows, a.history, a.json)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
