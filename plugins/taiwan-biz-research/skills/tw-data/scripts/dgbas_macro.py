#!/usr/bin/env python3
"""總體經濟指標 from DGBAS — GDP, CPI, unemployment, wages.

DGBAS has no REST API (statdb was decommissioned in 2021; nstatdb needs an
ASP.NET VIEWSTATE postback and isn't worth fighting). What it does have is
pre-generated XML with *more* history than the query system ever exposed —
GDP back to 1961Q1, CPI to 1981, unemployment to 1978. Keyless, UTF-8.

Two incompatible schemas live side by side, so this module reads both:

  flat   <DataCollection><失業率><年月別_Year_and_month>1978</…><總計_Total_百分比>1.67
         Wide. One element per period, fields as children. Used by 人力/薪資.

  sdmx   <Obs><Item>…</Item><TIME_PERIOD>1961Q1</TIME_PERIOD><TYPE>原始值</TYPE>
         Long. Each period appears twice — once 原始值, once 年增率(%).
         Used by GDP/CPI.

Usage:
    python3 dgbas_macro.py --unemployment          # 失業率
    python3 dgbas_macro.py --wage                  # 經常性薪資
    python3 dgbas_macro.py --gdp                   # 經濟成長率
    python3 dgbas_macro.py --cpi                   # 物價
    python3 dgbas_macro.py --gdp --items           # what series a file contains
    python3 dgbas_macro.py --gdp --history 12 --json
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET

from twdata._fetch import decode, fetch, strip_status

BASE = "https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/"

SERIES = {
    "unemployment": ("230038/mp0101a07.xml", "flat", "失業率", "總計_Total_百分比", "%"),
    "labour":       ("230038/mp0101a06.xml", "flat", "勞動力參與率", "總計_Total_百分比", "%"),
    "wage":         ("230037/mp05002.xml",   "flat", "經常性薪資", None, "元"),
    "total_wage":   ("230037/mp05001.xml",   "flat", "總薪資", None, "元"),
    "gdp":          ("230514/na8101a1q.xml", "sdmx", "經濟成長率", "經濟成長率(%)", "%"),
    "cpi":          ("230555/pr0101a1m.xml", "sdmx", "消費者物價指數", "總指數", ""),
}

# Annual rows interleave with monthly/quarterly ones in the same file (1978 then
# 1978M01). Anything without a period marker is the annual roll-up.
_SUB_ANNUAL = re.compile(r"(M\d{2}|Q[1-4]|\d{6})$")


def _num(v):
    try:
        return float(str(v).strip().replace(",", ""))
    except (TypeError, ValueError):
        return None


def parse_flat(xml_text, want_field=None):
    """<DataCollection><失業率><年月別…>…  → [{period, fields…}]"""
    root = ET.fromstring(xml_text)
    rows = []
    for rec in root:
        period, fields = None, {}
        for child in rec:
            tag, val = child.tag, (child.text or "").strip()
            if "年月別" in tag or "Year_and_month" in tag:
                period = strip_status(val)
            else:
                fields[tag] = val
        if period:
            rows.append({"period": period, **fields})
    return rows


def parse_sdmx(xml_text, item=None, type_="原始值"):
    """<Obs><Item>…<TIME_PERIOD>…<TYPE>原始值|年增率(%)  → [{period, value}]

    Items are matched by prefix, deliberately. CPI series carry their base
    period inside the name — '總指數(指數基期：民國110年=100)' — and DGBAS rebases
    every five years, so an exact match would silently return nothing the moment
    the base year moves to 民國115年.
    """
    root = ET.fromstring(xml_text)
    rows = []
    for obs in root.iter("Obs"):
        it = (obs.findtext("Item") or "").strip()
        if item and not it.startswith(item):
            continue
        if (obs.findtext("TYPE") or "").strip() != type_:
            continue
        v = _num(obs.findtext("Item_VALUE"))
        if v is None:
            continue
        rows.append({"period": strip_status(obs.findtext("TIME_PERIOD") or ""),
                     "item": it, "value": v})
    return rows


def sdmx_items(xml_text):
    root = ET.fromstring(xml_text)
    seen = []
    for obs in root.iter("Obs"):
        it = (obs.findtext("Item") or "").strip()
        if it and it not in seen:
            seen.append(it)
    return seen


def load(key, sub_annual_only=True):
    path, schema, label, field, unit = SERIES[key]
    text = decode(fetch(BASE + path))
    if schema == "flat":
        rows = parse_flat(text)
        if field:
            rows = [{"period": r["period"], "value": _num(r.get(field))} for r in rows]
            rows = [r for r in rows if r["value"] is not None]
        else:
            # 薪資 files vary in column naming; take the first numeric column.
            out = []
            for r in rows:
                for k, v in r.items():
                    if k == "period":
                        continue
                    n = _num(v)
                    if n is not None:
                        out.append({"period": r["period"], "value": n})
                        break
            rows = out
    else:
        rows = parse_sdmx(text, item=field)
        rows = [{"period": r["period"], "value": r["value"]} for r in rows]

    if sub_annual_only:
        sub = [r for r in rows if _SUB_ANNUAL.search(r["period"])]
        if sub:
            rows = sub
    return label, unit, rows, text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    for k in SERIES:
        g.add_argument(f"--{k.replace('_', '-')}", action="store_true")
    ap.add_argument("--history", type=int, default=8, metavar="N")
    ap.add_argument("--annual", action="store_true", help="annual rows instead of monthly/quarterly")
    ap.add_argument("--items", action="store_true", help="list the series inside an sdmx file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    key = next(k for k in SERIES if getattr(a, k.replace("-", "_")))
    path, schema, label, field, unit = SERIES[key]

    if a.items:
        if schema != "sdmx":
            raise SystemExit(f"--items only applies to sdmx files; {key} is flat")
        for it in sdmx_items(decode(fetch(BASE + path))):
            print(" ", it)
        return

    label, unit, rows, _ = load(key, sub_annual_only=not a.annual)
    if not rows:
        raise SystemExit(f"{label}: no rows parsed — the file layout may have changed")

    if a.json:
        print(json.dumps({"series": label, "unit": unit, "rows": rows[-a.history:]},
                         ensure_ascii=False, indent=2))
        return

    latest = rows[-1]
    print(f"{label}  最新 {latest['period']}: {latest['value']:,.2f}{unit}")
    print(f"  資料範圍 {rows[0]['period']} → {rows[-1]['period']}  ({len(rows):,} 期)")
    print(f"\n  近 {a.history} 期:")
    for r in rows[-a.history:]:
        print(f"    {r['period']:<10} {r['value']:>12,.2f}{unit}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
