#!/usr/bin/env python3
"""教育程度 — the strongest free proxy for purchasing power, down to the village.

內政部戶政司 ODRP020 gives the educational attainment of the 15+ population by
village (7,748 rows, 4 pages) — attainment is the best single proxy for spending
power, and this is the finest geography it's published at. Pairs cell-for-cell
with income_tax.py --village (same 區/里 grain) for an education × income map.

  python3 scripts/education.py --county            # 各縣市 大專以上/研究所 占比, ranked
  python3 scripts/education.py --district 臺北市    # by 鄉鎮市區 within a county
  python3 scripts/education.py --village 新竹市      # by 村里, ranked
  python3 scripts/education.py --county --json

"大專以上" = 專科+大學+研究所 (畢業). "研究所" = 碩士+博士 (畢業). Attainment counts
the graduated only; 肄業 (dropped out of a level) is not credited to it. Source is
the whole registered population, not a sample. Statistics are year-end (民國 yyy).
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys

from twdata._fetch import FetchError, fetch, decode

API = "https://www.ris.gov.tw/rs-opendata/api/v1/datastore/ODRP020/{year}?page={page}"

# graduated-only column groups (male + female), by tier
_GRAD = {
    "grad_school": ["edu_doctor_graduated_m", "edu_doctor_graduated_f",
                    "edu_master_graduated_m", "edu_master_graduated_f"],
    "university": ["edu_university_graduated_m", "edu_university_graduated_f"],
    "college": ["edu_juniorcollege_2ys_graduated_m", "edu_juniorcollege_2ys_graduated_f",
                "edu_juniorcollege_5ys_final2y_graduated_m",
                "edu_juniorcollege_5ys_final2y_graduated_f"],
}
_TOTAL = "edu_age_15up_total"


def _fetch_page(year: int, page: int, *, probe: bool = False) -> dict:
    body = fetch(API.format(year=year, page=page), min_bytes=50,
                 use_cache=not probe, freeze=not probe)
    return json.loads(decode(body))


def _fetch_all(year: int) -> list[dict]:
    """A closed year-end never changes → the per-page fetches freeze into cache."""
    first = _fetch_page(year, 1)
    if first.get("responseCode") != "OD-0101-S":
        raise FetchError(f"ODRP020/{year}: {first.get('responseCode')} {first.get('responseMessage')}")
    rows = list(first.get("responseData") or [])
    for p in range(2, int(first.get("totalPage", 1)) + 1):
        rows += _fetch_page(year, p).get("responseData") or []
    return rows


def _latest_year() -> int:
    roc = datetime.date.today().year - 1911
    for year in range(roc, roc - 5, -1):
        try:
            if _fetch_page(year, 1, probe=True).get("responseCode") == "OD-0101-S":
                return year
        except FetchError:
            continue
    raise SystemExit("ODRP020: 最近 5 個年度都抓不到 — 稍後重試。")


def _i(v) -> int:
    try:
        return int((v or "0").strip() or 0)
    except (ValueError, AttributeError):
        return 0


def _agg(rows: list[dict]) -> dict:
    """Sum the graduated-tier columns and the 15+ total over a set of rows."""
    a = {k: 0 for k in _GRAD}
    a["total"] = 0
    for r in rows:
        a["total"] += _i(r.get(_TOTAL))
        for tier, cols in _GRAD.items():
            a[tier] += sum(_i(r.get(c)) for c in cols)
    a["tertiary"] = a["grad_school"] + a["university"] + a["college"]
    a["tertiary_pct"] = (a["tertiary"] / a["total"] * 100) if a["total"] else None
    a["grad_school_pct"] = (a["grad_school"] / a["total"] * 100) if a["total"] else None
    return a


def _norm(s: str) -> str:
    return s.replace("台", "臺").strip()


def _county_of(site_id: str) -> str:
    return (site_id or "")[:3]            # 新北市板橋區 -> 新北市


def _rank_and_print(groups: dict, label: str, year: int, unit_label: str, as_json: bool):
    recs = []
    for name, rows in groups.items():
        a = _agg(rows)
        recs.append({unit_label: name, "pop_15up": a["total"],
                     "tertiary_pct": a["tertiary_pct"], "grad_school_pct": a["grad_school_pct"]})
    recs.sort(key=lambda r: -(r["tertiary_pct"] or 0))
    if as_json:
        print(json.dumps({"year_roc": year, "level": label, "units": recs},
                         ensure_ascii=False, indent=2))
        return recs
    print(f"教育程度 — {label} ({year}年, ODRP020 戶政司)")
    print(f"  {unit_label:<10}{'15歲以上人口':>12}{'大專以上%':>10}{'研究所%':>9}")
    for r in recs:
        pop = f"{r['pop_15up']:,}" if r["pop_15up"] else "—"
        t = f"{r['tertiary_pct']:.1f}" if r["tertiary_pct"] is not None else "—"
        g = f"{r['grad_school_pct']:.1f}" if r["grad_school_pct"] is not None else "—"
        print(f"  {r[unit_label][:10]:<10}{pop:>12}{t:>10}{g:>9}")
    return recs


def cmd_county(year: int | None, as_json: bool) -> None:
    year = year or _latest_year()
    rows = _fetch_all(year)
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(_county_of(r.get("site_id", "")), []).append(r)
    groups.pop("", None)
    _rank_and_print(groups, "各縣市", year, "縣市", as_json)
    if not as_json:
        print("\n  大專以上=專科+大學+研究所(畢業)/15歲以上人口。教育程度是購買力最強代理。")


def cmd_district(county: str, year: int | None, as_json: bool) -> None:
    year = year or _latest_year()
    cn = _norm(county)
    rows = [r for r in _fetch_all(year) if _norm(_county_of(r.get("site_id", ""))) == cn
            or cn in _norm(r.get("site_id", ""))]
    if not rows:
        raise SystemExit(f"找不到縣市 {county!r} (需全稱, 如 臺北市/新竹市)。")
    groups: dict[str, list] = {}
    for r in rows:
        groups.setdefault(_norm(r.get("site_id", "")), []).append(r)
    _rank_and_print(groups, f"{cn} 各鄉鎮市區", year, "鄉鎮區", as_json)


def cmd_village(county: str, year: int | None, top: int, as_json: bool) -> None:
    year = year or _latest_year()
    cn = _norm(county)
    recs = []
    for r in _fetch_all(year):
        area = _norm(r.get("site_id", ""))
        if not (area.startswith(cn) or cn in area):
            continue
        a = _agg([r])
        recs.append({"area": area, "village": (r.get("village") or "").strip(),
                     "pop_15up": a["total"], "tertiary_pct": a["tertiary_pct"],
                     "grad_school_pct": a["grad_school_pct"]})
    if not recs:
        raise SystemExit(f"找不到縣市 {county!r} 的村里資料。")
    recs.sort(key=lambda r: -(r["tertiary_pct"] or 0))
    if as_json:
        print(json.dumps({"year_roc": year, "county": cn, "village_count": len(recs),
                          "villages": recs}, ensure_ascii=False, indent=2))
        return
    print(f"{cn} 村里教育程度 ({year}年, ODRP020): {len(recs)} 村里")
    print(f"  {'區/里':<20}{'15+人口':>9}{'大專以上%':>10}{'研究所%':>9}")
    for r in recs[:top]:
        pop = f"{r['pop_15up']:,}" if r["pop_15up"] else "—"
        t = f"{r['tertiary_pct']:.1f}" if r["tertiary_pct"] is not None else "—"
        g = f"{r['grad_school_pct']:.1f}" if r["grad_school_pct"] is not None else "—"
        print(f"  {(r['area']+r['village'])[:20]:<20}{pop:>9}{t:>10}{g:>9}")
    print(f"\n  按大專以上占比排序, 前 {top}。可與 income_tax.py --village 同區里交叉(教育×所得)。")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--county", action="store_true", help="各縣市教育程度占比")
    g.add_argument("--district", metavar="縣市", help="某縣市各鄉鎮市區")
    g.add_argument("--village", metavar="縣市", help="某縣市各村里")
    ap.add_argument("--year", type=int, metavar="ROC", help="民國年度 (預設最新)")
    ap.add_argument("--top", type=int, default=20, metavar="N", help="--village 顯示前 N")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.county:
        cmd_county(a.year, a.json)
    elif a.district is not None:
        cmd_district(a.district, a.year, a.json)
    else:
        cmd_village(a.village, a.year, a.top, a.json)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
    except FetchError as e:
        print(f"FetchError: {e}", file=sys.stderr)
        sys.exit(1)
