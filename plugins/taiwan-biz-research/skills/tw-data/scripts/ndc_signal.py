#!/usr/bin/env python3
"""景氣對策信號 (business cycle light) + 領先/同時指標, from NDC.

Taiwan's single best free macro signal: a monthly composite score with a
traffic-light reading, plus the leading/coincident/lagging indices, back to
1984. This is the series to check first when someone asks "how is Taiwan's
economy doing right now".

Source: data.gov.tw dataset 6099 -> ws.ndc.gov.tw zip.
NDC's own site (index.ndc.gov.tw, www.ndc.gov.tw) is Cloudflare-403 to
non-browser clients, so the open-data route is the only reliable one.

Usage:
    python3 ndc_signal.py                 # latest reading + what's driving it
    python3 ndc_signal.py --history 24    # last 24 months
    python3 ndc_signal.py --json          # machine-readable
"""

import argparse
import json
import sys

from twdata._fetch import clean_cell, dataset_file, fetch, read_csv, resolve_dataset, unzip

DATASET = 6099

# 景氣對策信號 is scored 9-45 and bucketed into five lights. The official
# boundaries; a score alone is hard to read without them.
LIGHTS = [
    (38, 45, "紅", "熱絡", "景氣過熱，可能有政策緊縮風險"),
    (32, 37, "黃紅", "轉向", "景氣趨熱，注意是否過熱"),
    (23, 31, "綠", "穩定", "景氣穩定"),
    (17, 22, "黃藍", "轉向", "景氣趨弱，注意是否衰退"),
    (9, 16, "藍", "低迷", "景氣低迷"),
]


def light_meaning(score):
    for lo, hi, name, state, note in LIGHTS:
        if lo <= score <= hi:
            return name, state, note
    return "?", "?", f"分數 {score} 超出已知範圍 9-45"


def load():
    """Fetch and parse the NDC zip. Returns (main_rows, component_rows)."""
    meta = resolve_dataset(DATASET)
    zips = [d for d in meta["distribution"] if d["format"] == "ZIP"]
    if not zips:
        raise SystemExit(f"dataset {DATASET} has no ZIP distribution: {meta['distribution']}")
    files = unzip(fetch(zips[0]["url"]))

    def grab(name):
        for k, v in files.items():
            if k == name:
                return read_csv(v)
        raise SystemExit(f"{name} not in zip; got {list(files)}")

    return grab("景氣指標與燈號.csv"), grab("景氣對策信號構成項目.csv")


def clean_row(row):
    """Values before 1984 are '-'; the light column has a trailing space."""
    return {k: clean_cell(v) for k, v in row.items()}


def latest_with_light(rows):
    for row in reversed(rows):
        r = clean_row(row)
        if r.get("景氣對策信號綜合分數"):
            return r
    raise SystemExit("no scored month found")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--history", type=int, metavar="N", help="show the last N months")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    main_rows, comp_rows = load()
    latest = latest_with_light(main_rows)
    date = latest["Date"]
    score = int(float(latest["景氣對策信號綜合分數"]))
    light = latest["景氣對策信號"]
    name, state, note = light_meaning(score)

    comps = {}
    for row in comp_rows:
        if row["Date"] == date:
            comps = {k: clean_cell(v) for k, v in row.items() if k != "Date"}
            break

    if args.json:
        out = {
            "date": date, "score": score, "light": light,
            "state": state, "note": note,
            "leading_index": latest.get("領先指標綜合指數"),
            "coincident_index": latest.get("同時指標綜合指數"),
            "components": comps,
            "history": [clean_row(r) for r in main_rows[-args.history:]] if args.history else None,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    ym = f"{date[:4]}-{date[4:]}"
    print(f"景氣對策信號  {ym}")
    print(f"  燈號: {light}燈 ({state})  綜合分數: {score}/45")
    print(f"  {note}")
    print(f"  領先指標綜合指數: {latest.get('領先指標綜合指數')}")
    print(f"  同時指標綜合指數: {latest.get('同時指標綜合指數')}")

    if comps:
        print("\n  構成項目:")
        for k, v in comps.items():
            print(f"    {k:<34} {v if v is not None else '(未公布)'}")
        missing = [k for k, v in comps.items() if v is None]
        if missing:
            print(f"\n  註: {len(missing)} 項未公布 — 加班工時與製造業銷售量指數常缺，屬正常。")

    if args.history:
        print(f"\n  近 {args.history} 個月:")
        for r in main_rows[-args.history:]:
            r = clean_row(r)
            s, l = r.get("景氣對策信號綜合分數"), r.get("景氣對策信號")
            if s:
                d = r["Date"]
                print(f"    {d[:4]}-{d[4:]}  {int(float(s)):>2}分  {l}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
