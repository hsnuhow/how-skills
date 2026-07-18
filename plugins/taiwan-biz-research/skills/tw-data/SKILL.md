---
name: tw-data
description: Pull real Taiwan economic and market data for business-case research — the NDC business-cycle light (景氣對策信號/景氣燈號) and its driving components, leading/coincident indicators, and household income, spending and consumption mix by county and income quintile. Use this to answer "how is Taiwan's economy doing right now", "is the cycle turning", "how big is category X in Taiwan" (at the household survey's 10-category grain — no finer), "what do households in 新竹 spend", "size this market bottom-up", or whenever a Taiwan market-entry, competitor, investment or trend question needs numbers behind it rather than assertions. Coverage is strongest for consumer, manufacturing and export questions; pure services industries (media, education) are invisible to the fast monthly series. Also use it when someone asks where Taiwanese economic data comes from or whether a source is usable — this skill knows which endpoints are alive, which are traps, and why.
---

# Taiwan economic data

Real numbers for Taiwan business cases, from sources that are free, keyless and
verified working. Every endpoint here was called for real; the ones that look
plausible but are broken are listed at the bottom so you don't retry them.

## Two modes: quick data-integration vs full analysis

**Quick mode (資料整合問答) — the default.** When the ask is a *value*, a
*combined table*, or "where does X come from / can I get it", answer straight
from this skill's scripts and reference indexes. Do NOT spin up a case study.

- a number or series → run the matching script (`ndc_signal.py`, `household.py`,
  `mof_industry.py`, `dgbas_macro.py`, `moea_orders.py`, `twse_revenue.py`)
- "is there data on X / where" → `references/datasets.md` (breadth: agency → datasets)
- "what columns / how do I pull X" → `references/schemas.md` (depth: fields, units, traps)
- integrate several sources → run each script, join, and state the period/unit
  mismatches explicitly

This path is seconds to a few minutes and never fans out to sub-agents. Caching
(`tw_cache.py`) makes repeat pulls near-instant. **When someone asks a
data-integration question, stay here — don't escalate.**

**Full analysis.** When the ask is a *recommendation* (enter or not, invest or
not, how big, who wins), that's `biz-case-workflow` — hypothesis-driven,
20+ agents, tens of minutes. The test: if the answer is a value or an integrated
table → quick mode; if the answer is a *choice* → full analysis.

## Start here: why this exists

**Taiwan is missing from the international databases.** It is not a World Bank
member and has no WDI entry — it's the largest economy outside the system. The
IMF dropped it in 1980; it isn't in the OECD. FRED carries ~360 Taiwan series,
but they are annual, sourced from Penn World Table / IMF WEO, and lag by 1-2
years. **There is no monthly Taiwan macro on FRED.**

So the usual move — reach for a World Bank or FRED MCP — produces nothing usable
for anything current. Taiwan data has to come from Taiwanese sources directly,
and those have sharp edges. That is what this skill is for.

## The rule that matters most

**HTTP 200 does not mean you got data.** Taiwanese government hosts answer 200
with HTML error pages, bot challenges, empty bodies, and header-only files for
months that aren't published yet. `scripts/twdata/_fetch.py` validates every
payload — size, content signatures, response codes — and raises `FetchError`
rather than handing back junk. Use it for any new endpoint; do not write a bare
`requests.get`.

It also absorbs the other recurring traps, so callers never think about them:
percent-encoding Chinese filenames in URLs, the `ws.dgbas.gov.tw` broken
certificate chain, UA filtering, `utf-8-sig` BOMs, Big5 zip filenames, ROC↔AD
dates, and DGBAS's Ⓡ/Ⓟ revision suffixes. See `references/pitfalls.md` for what
each one is and why.

## What you can get

### 景氣對策信號 — the cycle light (`scripts/ndc_signal.py`)

Taiwan's best free macro signal: a 9-45 composite score bucketed into five
lights, monthly, back to 1984. Check this first for "how is the economy doing".

```bash
python3 scripts/ndc_signal.py                # latest light, score, and components
python3 scripts/ndc_signal.py --history 24   # last 24 months
python3 scripts/ndc_signal.py --json
```

It returns the component breakdown too (M1B, 股價指數, 工業生產指數, 海關出口值,
批發零售餐飲營業額 …), so you can say *which* component is driving a turn rather
than just quoting the colour. Two components — 加班工時 and 製造業銷售量指數 —
are routinely blank in the latest month; that's normal, not a bug.

Lights: 藍 9-16 低迷 · 黃藍 17-22 轉向 · 綠 23-31 穩定 · 黃紅 32-37 轉向 · 紅 38-45 熱絡.

### 家庭收支調查 — income, spending, and the category mix (`scripts/household.py`)

The backbone of bottom-up market sizing, and free.

```bash
python3 scripts/household.py --spend            # spend + 消費率 by county
python3 scripts/household.py --mix              # category mix, 1976 → latest
python3 scripts/household.py --quintile         # income quintiles
python3 scripts/household.py --tam 醫療保健      # size a category by county
python3 scripts/household.py --tam 餐廳及住宿 --json
```

`--tam` computes `county households × spend per household × category share`,
aggregated to a national total. Households come from MOI at village level and
are rolled up to county; only 普通住戶 (共同生活戶 + 單獨生活戶) are counted —
共同事業戶 are institutional and have no family budget.

Categories available to `--tam`: 食品飲料及菸草, 衣著鞋襪類, 住宅服務水電瓦斯及其他燃料,
家具設備及家務維護, 醫療保健, 交通及資通訊, 休閒、運動、文化及教育, 餐廳及住宿,
保險及金融服務, 其他. Pass any substring; run `--mix` to see current shares.

**State the caveat when you use this**: 家庭收支調查 covers household consumption
only — no corporate purchasing, no government spending. It is the right base for
consumer categories and the wrong one for B2B or infrastructure.

### 上市公司月營收 — the monthly demand tracker (`scripts/twse_revenue.py`)

Every listed company reports revenue by the 10th of the following month, and the
feed carries 產業別 per row — so rolling it up gives an industry-level monthly YoY
series that is usually a paid product.

```bash
python3 scripts/twse_revenue.py                 # industry roll-up, sorted by YoY
python3 scripts/twse_revenue.py --top 15        # fastest-growing companies
python3 scripts/twse_revenue.py --bottom 15     # sharpest decliners
python3 scripts/twse_revenue.py --industry 半導體業
python3 scripts/twse_revenue.py --company 2330
```

Industry YoY is computed from summed revenue, not averaged across companies —
averaging would weight a NT$50m company like TSMC. `--min-revenue` (default 1億)
filters the tiny bases that otherwise dominate any YoY ranking with noise.

**This endpoint is a current-month snapshot with no history.** Poll monthly and
accumulate, or backfill from MOPS. Listed companies only — Taiwan's SME economy
is invisible here.

### 總經 — GDP, CPI, 失業率, 薪資 (`scripts/dgbas_macro.py`)

```bash
python3 scripts/dgbas_macro.py --gdp            # 經濟成長率, 1962Q1-
python3 scripts/dgbas_macro.py --cpi            # 物價, 1981M01-
python3 scripts/dgbas_macro.py --unemployment   # 失業率, 1978M01-
python3 scripts/dgbas_macro.py --wage           # 經常性薪資, 198001-
python3 scripts/dgbas_macro.py --gdp --items    # what else is in that file
```

`--items` is worth knowing: the GDP file also carries 平均每人GDP, GNI, 平均匯率,
期中人口; the CPI file breaks down to 食物類 → 穀類 → 米類. Use `--items` to find
a series rather than guessing its name.

### 營業稅銷售額按行業別 — the SME-inclusive read (`scripts/mof_industry.py`)

The one series that sees what TWSE cannot: every VAT-registered business,
including the SMEs and services that make up most of Taiwan's economy.

```bash
python3 scripts/mof_industry.py --list 出版          # find the industry name
python3 scripts/mof_industry.py --industry 581       # national 3-digit monthly series
python3 scripts/mof_industry.py --industry 581 --history 12
python3 scripts/mof_industry.py --county 批發        # a major-category across 22 counties
```

Digit keywords match the industry code exactly; text matches names as a
substring — and matches are never summed, because the file holds aggregates and
their children in one column (58 contains 581 and 582), the same trap as MOEA
sectors.

**Source note (2026-07):** the old web02 sys=220 cube (3-digit × county in one
cell) is down — its report engine hangs while the host stays up. This now reads
the 財政統計月報 static Excel on service.mof.gov.tw instead, which splits that cube
into two projections: `--industry` gives 3-digit × month **national** (表3-9),
`--county` gives major-category × 22 counties × month (表3-11). 3-digit × county
in one cell is not available from any live free source until sys=220 revives — use
national 3-digit or county major-category and say which. Unit is 百萬元, coverage
112年 (2023) onward. Full detail + the outage record in `references/endpoints.md`.

**Use this when the four fast reads are blind** — media, education, professional
services, any fragmented consumer category. A worked contrast: `--tam 休閒`
gives a NT$5,400億 bucket, while `--industry 581` shows the entire news/magazine
/book publishing industry is ~NT$460億/year — the grain warning made real.

**Caveats it prints and you must keep**: 口徑 is self-reported 稅籍行業別;
營業稅法第8條 exempts magazines' own-publication sales and ad revenue, so 58x
publishing is structurally understated; VAT files bimonthly (odd months are
tiny — use annual or cumulative rows).

### 綜合所得稅 — purchasing power by county, tier and village (`scripts/income_tax.py`)

The whole filing population, not a survey sample — a fuller income map than 家庭收支
調查, and the backbone of purchasing-power tiering.

```bash
python3 scripts/income_tax.py --county            # 各縣市: 戶數/總所得/人均/有效稅率
python3 scripts/income_tax.py --structure         # 薪資 vs 股利 share, all counties
python3 scripts/income_tax.py --structure 臺北市   # full income composition for one county
python3 scripts/income_tax.py --village 新竹市      # village-level mean/median income
```

`--county` ranks per-household income (新竹市 164萬/戶 tops 臺北 149萬 — 竹科);
`--structure` exposes salary-vs-capital mix (臺北 股利占比 29.9% — the most capital
income, high earners with low spend propensity); `--village` is the finest income
geography Taiwan publishes (482 里 in 臺北). Amounts 千元, shown as 億 / 萬元/戶.
The filing unit is a 納稅單位, not a 家庭收支 household; stats lag ~3 years; 加計股利
新口徑 is 107年 onward. Rollup rows (合計/其他) are filtered out.

### 教育程度 — purchasing-power proxy to the village (`scripts/education.py`)

Educational attainment is the strongest free proxy for spending power, and 戶政司
ODRP020 publishes it by village (7,748 rows, 4 pages).

```bash
python3 scripts/education.py --county          # 各縣市 大專以上/研究所 占比, ranked
python3 scripts/education.py --district 臺北市   # by 鄉鎮市區
python3 scripts/education.py --village 新竹市     # by 村里, ranked
```

`--county` ranks 大專以上 share (臺北 57.3%, 新竹市 研究所 14.2% — 竹科). Its real
power is the cross-check with income: 新竹市東區關新里 tops both 研究所占比 (42.8%)
and per-household income (460萬) — two independent registers (戶政 vs 財稅) agreeing
cell-for-cell. Pairs with `income_tax.py --village` on the same 區/里 for an
education × income map. Whole registered population; 大專以上 = 專科+大學+研究所 畢業.

### 外銷訂單、生產、零售 (`scripts/moea_orders.py`)

外銷訂單 is the best leading indicator here — orders are booked before they are
produced or shipped, so this turns first.

```bash
python3 scripts/moea_orders.py --orders 電子      # 電子產品外銷訂單, 1984-
python3 scripts/moea_orders.py --orders 資通訊
python3 scripts/moea_orders.py --production      # 製造業生產價值指數, 1982-
python3 scripts/moea_orders.py --production --sectors          # list 行業別
python3 scripts/moea_orders.py --production --sector 電子零組件製造業
python3 scripts/moea_orders.py --retail          # 零售營業額指數
```

**Always `--sectors` before `--sector`.** The names are not what you'd guess:
it's 電子零組件製造業, not 電子零組件業. The filter is an exact match on purpose —
these files hold the aggregate and its sub-industries in one column, and a
substring match silently merges 製造業 with 其他製造業 and returns a wrong number
with duplicate periods as the only symptom.

## Using this in a business case

The data is the easy half. What makes it consulting-grade:

- **Lead with the signal, then decompose.** "紅燈, 39/45, six months running"
  is the headline; the component table is what makes it an argument.
- **Pair a structural series with a fast one.** 家庭收支調查 is annual and deep —
  it tells you how the market is *shaped*. It cannot tell you what happened last
  quarter. For that you need the monthly series (see Not yet built).
- **Anchor every number to its year.** These sources publish on different lags:
  the cycle light runs ~2 months behind, 家庭收支 ~18 months, MOI households ~1
  year. A table mixing 2024 spend with 2025 households is fine — say so.
- **Bottom-up sizing beats a cited total.** A number you built from households ×
  spend × share is defensible line by line. Sanity-check it against a published
  aggregate (MOEA 營業額) and explain any gap rather than hiding it.

## What is deliberately not here

Sources that look useful and are not:

- **Goodinfo / 財報狗** — active anti-scraping, ToS not readable, and
  unnecessary: the underlying data is free and keyless from TWSE.
- **`twder`** (匯率) — looks maintained on GitHub, but `master` hasn't been
  touched since 2021; the activity is unmerged bot branches. Dead.
- **World Bank / IMF / OECD MCPs** — no Taiwan.
- **`statdb.dgbas.gov.tw`** — decommissioned 2021, still answers 200 with a Big5
  notice. **`dmz26.moea.gov.tw`** — no DNS. **`cpx.cbc.gov.tw/.../DataSet`** —
  200 with an empty body for every set_id. **`rate.bot.com.tw`** — Akamai
  challenge; use CBC's `FTDOpenData015.csv` instead.
- **data.gov.tw keyword search** — the search API needs a key and the useful
  economic datasets number about twenty. Resolve by id (`resolve_dataset`)
  instead; the full 37,957-row catalogue is 68% administrative records.

## Corroborate before you conclude

The scripts cover four independent reads on the same economy — the cycle light,
listed-company revenue, export orders, and production/retail. **Check them
against each other before putting a claim in a deck.** When they agree, the
finding is solid; when they diverge, the divergence *is* the finding.

**One shared blind spot: all four reads lean manufacturing / export / retail.**
A pure services industry — media, education, professional services — is
invisible in every fast series here: TWSE's 33 產業別 carry no 出版/媒體/文創,
and MOEA production is manufacturing-only. Four thermometers can't measure a
patient who isn't in the room; for those industries reach for `mof_industry.py`
(營業稅 by industry — includes SMEs and services) instead of proxying with retail.

The current picture is a worked example: 外銷訂單 電子 +61%, 上市月營收 +45%,
製造業生產 +10%, 零售營業額 +3%, and 民生工業 production actually negative —
while the cycle light sits at 紅 for six straight months. Four sources agreeing
on a boom, and the same four showing it is an export/electronics boom that
domestic demand is not sharing. Neither half of that is visible from one series.

## Off-API but verified

Advertising market size (DMA), willingness to pay (Reuters DNR), industry survey
output (TAICCA), and the WIRED.tw precedent live outside open data but are
verified with URLs, retrieval methods and dated snapshots in
`references/external-sources.md`. Media and subscription cases need them.

## Not yet built

Verified working, wrapper not written — endpoints are in `references/endpoints.md`:

- **CIER PMI/NMI** — free monthly Excel, the best free leading indicator after
  外銷訂單. Needs a URL-discovery step (the short paths 404).
- **NCCC 信用卡消費** — real transactions by 縣市 × 產業 × 性別 × 職業, monthly.
  The best free consumer granularity; pairs with 家庭收支 (structural) as the
  fast-moving half.
- **PCC 政府採購** — B2G demand, same-day via the community API.
- **GCIS 公司登記** — entity resolution by 統編.
- **TPEx** (上櫃, 225 endpoints) — mixes ROC and AD dates across endpoints;
  spec at `/openapi/swagger.json`, unknown paths 302 to an HTML homepage.
- **推銷費用 per company** — the ad-market *demand* side. Not in any OpenAPI
  summary (those carry 營業費用 total only); comes from MOPS inline-XBRL
  statements, one GET per company-quarter, Big5. Endpoint + regex in
  `references/endpoints.md`. Pairs with DMA (supply side) for advertising cases.
