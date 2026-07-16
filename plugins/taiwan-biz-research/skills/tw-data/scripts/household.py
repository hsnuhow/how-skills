#!/usr/bin/env python3
"""家庭收支調查 — regional household income, spending and its category mix.

This is the backbone of bottom-up market sizing in Taiwan, and it is free.
Combine three of these series and you can size a category, by county, by income
tier, without buying anything:

    county households x avg household spend x category share = category TAM

Datasets (DGBAS, via data.gov.tw; all CSV, AD years, utf-8-sig):
    9420  平均每戶消費支出按區域別分        1998-      spend per household by county
    9415  各縣市別平均每戶可支配所得         1998-      disposable income by county
    6588  家庭消費支出結構按消費型態分        1976-      category mix (食/衣/住/行/醫/樂...)
    6565  戶數五等分位組之可支配所得、消費支出   1976-      income quintiles

Household counts come from MOI (內政部戶政司), which serves village-level data
and needs aggregating up to county.

Usage:
    python3 household.py --spend                 # spend by county, latest year
    python3 household.py --mix                   # category mix, latest + 1976 baseline
    python3 household.py --quintile              # income quintiles
    python3 household.py --tam 醫療保健           # size a category by county
    python3 household.py --tam 醫療保健 --json
"""

import argparse
import json
import sys

from twdata._fetch import FetchError, clean_cell, dataset_file, fetch, read_csv_rows

SPEND_BY_COUNTY = 9420
INCOME_BY_COUNTY = 9415
CATEGORY_MIX = 6588
QUINTILE = 6565

# MOI household registry. ROC year is a mandatory path segment, page-based
# pagination only ($top is silently ignored), errors arrive as HTTP 200 with a
# responseCode in the body.
MOI_URL = "https://www.ris.gov.tw/rs-opendata/api/v1/datastore/ODRP019/{roc}?page={page}"


def _wide_table(dataset_id, contains=""):
    """These datasets are wide: first column is the year, the rest are series."""
    rows = read_csv_rows(dataset_file(dataset_id, fmt="CSV", contains=contains))
    header = [h.strip() for h in rows[0]]
    data = []
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        data.append({header[i]: clean_cell(v) for i, v in enumerate(r) if i < len(header)})
    return header, data


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def spend_by_county():
    header, rows = _wide_table(SPEND_BY_COUNTY)
    latest = rows[-1]
    counties = {k.replace("-元", ""): _num(v) for k, v in latest.items()
                if k != "年" and k.endswith("-元") and _num(v)}
    return latest["年"], counties


def income_by_county():
    try:
        header, rows = _wide_table(INCOME_BY_COUNTY)
    except FetchError as e:
        return None, {}
    latest = rows[-1]
    counties = {k.replace("-元", ""): _num(v) for k, v in latest.items()
                if k != "年" and k.endswith("-元") and _num(v)}
    return latest["年"], counties


def category_mix():
    """Share of household spending by category. Returns (year, {category: pct})."""
    header, rows = _wide_table(CATEGORY_MIX)
    latest = rows[-1]
    mix = {k.replace("-百分比", ""): _num(v) for k, v in latest.items()
           if k != "年" and k != "合計-百分比" and _num(v) is not None}
    return latest["年"], mix, rows


# MOI's response schema is not stable across years. ROC 114 serves English keys
# (site_id, household_ordinary_total); ROC 113 serves Chinese ones (區域別,
# 共同生活戶_戶數). Same endpoint, same dataset, different field names — so read
# both spellings rather than assuming either.
MOI_FIELDS = {
    "county": ("site_id", "區域別"),
    # A household for market-sizing purposes is 普通住戶: people living together
    # plus people living alone. 共同事業戶 (institutional/business households —
    # dormitories, barracks) are excluded; they don't have a family budget.
    "counts": (
        ("household_ordinary_total", "共同生活戶_戶數"),
        ("household_single_total", "單獨生活戶_戶數"),
    ),
}

MOI_OK = "OD-0101-S"        # 處理完成
MOI_NO_DATA = "OD-0102-S"   # 查無資料 — the year isn't published yet


def _pick(record, names):
    for n in names:
        if n in record:
            return record[n]
    return None


def household_counts():
    """County household counts from MOI, aggregated up from village level.

    MOI publishes on a lag, so walk back from the current ROC year until one
    resolves (ROC 115 currently answers 查無資料). Every Taiwanese county name is
    exactly three characters, which makes slicing site_id ('新北市板橋區') safe.
    """
    from datetime import date

    for roc in range(date.today().year - 1911, date.today().year - 1911 - 4, -1):
        page, total = 1, {}
        try:
            while True:
                body = fetch(MOI_URL.format(roc=roc, page=page), min_bytes=64)
                payload = json.loads(body.decode("utf-8-sig"))
                code = payload.get("responseCode")
                if code == MOI_NO_DATA:
                    total = {}
                    break
                if code != MOI_OK:
                    raise FetchError(f"MOI responseCode={code} {payload.get('responseMessage')}")

                recs = payload.get("responseData") or []
                if not recs:
                    break
                for r in recs:
                    county = (_pick(r, MOI_FIELDS["county"]) or "")[:3]
                    if not county:
                        continue
                    n = sum(_num(_pick(r, names)) or 0 for names in MOI_FIELDS["counts"])
                    if n:
                        total[county] = total.get(county, 0) + n

                if page >= int(payload.get("totalPage") or 1):
                    break
                page += 1
            if total:
                return roc + 1911, total
        except (FetchError, json.JSONDecodeError, KeyError, ValueError):
            continue
    return None, {}


def cmd_spend():
    year, counties = spend_by_county()
    iyear, incomes = income_by_county()
    print(f"平均每戶消費支出 by 縣市 ({year} 年, 元/戶)")
    for name, v in sorted(counties.items(), key=lambda x: -x[1]):
        inc = incomes.get(name)
        rate = f"  消費率 {v / inc * 100:5.1f}%" if inc else ""
        print(f"  {name:<10} {v:>10,.0f}{rate}")


def cmd_mix():
    year, mix, rows = category_mix()
    base = {k.replace("-百分比", ""): _num(v) for k, v in rows[0].items()
            if k not in ("年", "合計-百分比") and _num(v) is not None}
    print(f"家庭消費支出結構 ({rows[0]['年']} → {year})")
    print(f"  {'類別':<26}{rows[0]['年']:>8}{year:>8}   變化")
    for k, v in sorted(mix.items(), key=lambda x: -x[1]):
        b = base.get(k)
        delta = f"{v - b:+6.1f}pp" if b is not None else "     —"
        bs = f"{b:>7.2f}%" if b is not None else "      —"
        print(f"  {k:<26}{bs}{v:>7.2f}%  {delta}")


def cmd_quintile():
    header, rows = _wide_table(QUINTILE)
    latest = rows[-1]
    print(f"戶數五等分位 ({latest['年']} 年)")
    for k, v in latest.items():
        if k != "年" and v:
            print(f"  {k:<44} {v:>12}")


def cmd_tam(category, as_json=False):
    year, counties = spend_by_county()
    myear, mix, _ = category_mix()

    matches = [k for k in mix if category in k]
    if not matches:
        raise SystemExit(f"找不到類別 {category!r}。可用類別:\n  " + "\n  ".join(mix))
    cat = matches[0]
    share = mix[cat] / 100.0

    hyear, households = household_counts()
    if not households:
        print("⚠️  戶數抓取失敗 — 只輸出每戶金額，無法推總市場規模。", file=sys.stderr)

    rows = []
    for name, spend in sorted(counties.items(), key=lambda x: -x[1]):
        if name == "臺灣地區":
            continue
        per_hh = spend * share
        hh = households.get(name)
        rows.append({
            "county": name, "households": hh,
            "spend_per_household": round(spend),
            "category_spend_per_household": round(per_hh),
            "market_size_ntd": round(per_hh * hh) if hh else None,
        })

    if as_json:
        print(json.dumps({
            "category": cat, "share_pct": mix[cat],
            "spend_year": year, "mix_year": myear, "household_year": hyear,
            "counties": rows,
        }, ensure_ascii=False, indent=2))
        return

    total = sum(r["market_size_ntd"] for r in rows if r["market_size_ntd"])
    print(f"市場規模估算 — {cat}")
    print(f"  消費結構占比 {mix[cat]:.2f}% ({myear})  ×  每戶消費支出 ({year})  ×  戶數 ({hyear or 'n/a'})\n")
    print(f"  {'縣市':<10}{'戶數':>10}{'每戶該類支出':>14}{'市場規模(億元)':>16}")
    for r in rows:
        hh = f"{r['households']:,.0f}" if r["households"] else "—"
        ms = f"{r['market_size_ntd'] / 1e8:,.1f}" if r["market_size_ntd"] else "—"
        print(f"  {r['county']:<10}{hh:>10}{r['category_spend_per_household']:>14,}{ms:>16}")
    if total:
        print(f"\n  合計 ≈ NT$ {total / 1e8:,.0f} 億元")
    print("\n  註: 這是由下而上的推估 — 家庭消費支出僅涵蓋家戶消費，不含企業採購與政府支出。")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--spend", action="store_true", help="每戶消費支出 by 縣市")
    g.add_argument("--mix", action="store_true", help="消費支出結構 (類別占比)")
    g.add_argument("--quintile", action="store_true", help="所得五等分位")
    g.add_argument("--tam", metavar="類別", help="估算某消費類別的市場規模")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.spend:
        cmd_spend()
    elif a.mix:
        cmd_mix()
    elif a.quintile:
        cmd_quintile()
    elif a.tam:
        cmd_tam(a.tam, a.json)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
