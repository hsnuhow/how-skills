# Verified Taiwan data endpoints

Every row below was fetched successfully while building this skill. All are free
and keyless unless noted. Wrapped = a script in `../scripts/` already handles it;
otherwise use `twdata/_fetch.py` directly — it absorbs the pitfalls.

**This file answers "what exists, where, and how it breaks." For the exact
columns — real headers, units, sample rows, verified latest period — see
[`schemas.md`](schemas.md)**, the index to a per-source schema catalogue in
`schemas/` (live-fetch sweep, 2026-07-18). Open only the one file you need;
the set totals ~190 KB. Read the target's schema before writing a parser —
several entries below were corrected by that sweep.

## Wrapped

| Signal | Source | Depth | Script |
|---|---|---|---|
| 景氣對策信號 + 領先/同時/落後指標 + 構成項目 | data.gov.tw `6099` → `ws.ndc.gov.tw` ZIP | **1984→** monthly | `ndc_signal.py` |
| 平均每戶消費支出按區域別 | data.gov.tw `9420` (DGBAS CSV) | 1998→ annual | `household.py --spend` |
| 各縣市別平均每戶可支配所得 | data.gov.tw `9415` | 1998→ annual | `household.py --spend` |
| 家庭消費支出結構按消費型態 | data.gov.tw `6588` | **1976→** annual | `household.py --mix` |
| 戶數五等分位之可支配所得/消費支出/儲蓄 | data.gov.tw `6565` | **1976→** annual | `household.py --quintile` |
| 縣市戶數 (村里級彙總) | `ris.gov.tw/rs-opendata/api/v1/datastore/ODRP019/{ROC}?page=N` | 107→ annual | `household.py` |
| 營業稅銷售額按行業別 (3碼小類 × 22縣市, **含SME**) | `web02.mof.gov.tw/njswww/webMain.aspx?…funid=i0520…` CSV | 107→ monthly | `mof_industry.py` |

## Verified, not yet wrapped

**TWSE OpenAPI** — `openapi.twse.com.tw/v1/`, 143 endpoints, no key.
`swagger.json` is 306 KB. All values are strings; dates are ROC.
- `opendata/t187ap05_L` — 上市月營收, all companies (~596 KB). **Current-month
  snapshot, no history** — poll monthly and accumulate.
- `opendata/t187ap05_P` — 公發. `exchangeReport/STOCK_DAY_ALL` — 1,370 rows/day.
- Backfill history from MOPS: `mopsov.twse.com.tw/nas/t21/sii/t21sc03_{ROC}_{M}_0.html`
  (Big5; `mops.twse.com.tw/mops/web/t21sc03` is dead). A 916-byte response means
  the month isn't published.

**TPEx OpenAPI** — `www.tpex.org.tw/openapi/v1/`, 225 endpoints, no key.
Mixes ROC and AD dates across endpoints. The spec lives at
`/openapi/swagger.json` (NOT under `/v1/`); MOPS-sourced endpoints are prefixed
`/v1/mopsfin_*` (上櫃 `_O_`, 興櫃 `_U_`). **Unknown API paths 302-redirect to
the HTML homepage — with `-L` that's a 200 + 22KB of HTML that isn't data.**

**Income statements via OpenAPI — 推銷費用 is NOT there.** Verified 2026-07:
TWSE `opendata/t187ap06_L_ci` (上市一般業, ~1,043 rows/quarter), TPEx
`mopsfin_t187ap06_O_ci{,A}` (上櫃), `_U_` (興櫃), `_X_` (公發) all carry one
**營業費用 total only** — no 推銷/管理/研發 split. Units 千元, dates ROC,
quarterly. Fine for margin roll-ups, useless for a marketing-spend series.

**MOPS inline-XBRL statements — the real 推銷費用 path.** Per company per
quarter, plain GET, fully programmatic:
`mopsov.twse.com.tw/server-java/t164sb01?step=1&CO_ID={code}&SYEAR={AD}&SSEASON={1-4}&REPORT_ID=C`
Despite the name it serves the full statement set; the P&L lines carry inline
XBRL tags — regex `name="ifrs-full:SellingExpense"[^>]*>([\d,]+)` and likewise
`AdministrativeExpense`, `ResearchAndDevelopmentExpense`, `Revenue`. Verified:
2330 2025Q1 → selling 3,754,815 / admin 24,883,748 / R&D 56,547,493 千元.
Traps: body is **Big5** (decode before searching, or every keyword "misses");
`REPORT_ID=A` (個體) on a quarter returns **200 + 98 bytes** — quarterly filings
are consolidated-only, standalone exists annually. Cost note: one request per
company-quarter — cheap for a competitor set, ~1,000 requests to index the
whole market.

口徑 for marketing-spend uses: 推銷費用 bundles sales salaries, logistics and
freight with advertising — it is marketing-intensity, not ad spend. And the
consolidated statement folds in overseas subsidiaries; **no free source splits
selling expense by subsidiary** (that detail lives in 財報附註 PDFs only), so
"how much of the marketing is booked offshore" is answerable only annually as
consolidated-minus-standalone, and only roughly.

**DGBAS macro XML** — `ws.dgbas.gov.tw/001/Upload/461/relfile/…`, keyless, UTF-8.
No REST API exists (`statdb` decommissioned; `nstatdb` needs ASP.NET VIEWSTATE),
but these pre-generated files go deeper than the query system did.

| Series | Path | Rows | Depth |
|---|---|---|---|
| 失業率 | `11525/230038/mp0101a07.xml` | 630 | 1978→ |
| 勞動力參與率 | `11525/230038/mp0101a06.xml` | 630 | 1978→ |
| 經常性薪資 | `11525/230037/mp05002.xml` | 604 | 1980→ |
| 總薪資 | `11525/230037/mp05001.xml` | 604 | 1980→ |
| GDP 季 | `11525/230514/na8101a1q.xml` | 7,830 | **1961Q1→** |
| CPI | `11525/230555/pr0101a1m.xml` | 88,452 | 1981M01→ (15.7 MB — stream) |

Two incompatible schemas: GDP/CPI use SDMX-ish `<Obs><Item><TIME_PERIOD>`;
人力/薪資 use flat `<DataCollection><失業率>`. Annual rows interleave with monthly
in the same file (`1978` then `1978M01`) — filter by pattern. Each period appears
twice (`TYPE` = 原始值 / 年增率).

**MOEA** — `service.moea.gov.tw/EE520/opendata/{中文檔名}.csv`, UTF-8 BOM, ROC
`YYYMM`. The HTML portal is CF-403; these CSVs are not.
- **製造業生產價值指數** (`16366`, 1.19 MB, →1982-01) — NOT the industrial
  production index. It is a **nominal value** index (基期 110年=100), so price
  and volume cannot be separated; reading it as "output" overstates any
  period when prices rose. Manufacturing (C) only — no mining, no utilities.
  32 分類 with 四大工業群 (I1-I4) mixed into the same 行業別 column.
- 批發零售及餐飲業營業額指數 (`16365`, 870 KB) — released 23rd-26th of the next month.
  38 業別, 基期 110年=100, **nominal — no real/price column, deflate externally**
  (CPI 總指數 overstates 綜合商品零售 by ~1.8pp; use the matching CPI 基本分類).
  `餐館` and `飲料店` have no 業 suffix while their sibling `外燴及團膳承包業` does.
- 外銷訂單: 電子產品 (`16362`) / 資通訊 (`16361`), →1984-01

**CBC** — `www.cbc.gov.tw/public/data/OpenData/…` (URL-encode the Chinese dirs).
**The one agency using AD dates.** Its OpenAPI is a trap (200 + empty body).
- M1A/M1B/M2: `經研處/EF15M01.csv` — 1987M05→
- 匯率 NTD/USD daily: `外匯局/FTDOpenData015.csv` — 4,607 rows, 20080102→
- 利率: `業務局/xl/XOpen3.csv` — 2003→

**MOF** — 進出口貿易 `opendata.customs.gov.tw/data/6053/csv.csv` (CSV only;
`json.json` 404s). 營業稅 by industry comes in two flavours, verified 2026-07:

- **`eip.fia.gov.tw/OAI/api/businessTaxAutoApplyRpt?limit=1500&offset=0`** —
  dataset 8356, annual 2010→, JSON, units 元. Clean API but the classification
  is the 營業稅特種 40 類 (no J58 detail). `limit` caps at **1500**; exceeding it
  returns 200 with a *double-encoded* JSON error string. `offset` past the end
  returns **404 + empty body**, not 200 — pagination must check both. A
  `/{dataYear}` path variant takes AD years and needs no limit/offset. Swagger
  for all 11 datasets: `/OAI/v2/api-docs`.
- **`web02.mof.gov.tw/njswww/webMain.aspx?sys=220&…&funid=i0520&…&utf=1`** —
  the 財政統計資料庫 CSV export, monthly 107→, 3-digit 稅務行業小類 (581 新聞、
  雜誌、期刊、書籍及其他出版業) × 22 counties, units 千元. **This is the only
  free read on an industry's revenue that includes SMEs and services** — the
  complement to TWSE's listed-only view. Wrapped: `mof_industry.py`.
  Traps (all handled by the script): funid binds a classification revision to a
  year span (i0509 = 107-111 / 8th revision, i0520 = 112-116 / 9th — J 大類 was
  renamed across the seam, joins need mapping); **asking a funid for a year it
  doesn't cover silently returns its newest year, HTTP 200, bytes identical to
  the real file — validate the periods in the body, never trust `ym`**; `(D)` =
  保密隱匿, `－` = none, negatives are real (銷售折讓); VAT files bimonthly so
  odd months are tiny; `utf=1` required (BOM); host occasionally drops
  connections — retry once. 營業稅法第8條 exempts magazines' own sales + ad
  revenue, so 58x is structurally understated.

**MOL** — `apiservice.mol.gov.tw/OdService/rest/dataset` → 860 dataset ids;
`/datastore/{id}` for data. `?modified=yyyy-MM-dd` for incremental sync.

**CIER PMI/NMI** — free monthly Excel with full history at
`cier.edu.tw/en/eco_cat/pmi-en/` and `/nmi-en/`. **Resolve from the page — the
short `/pmi` and `/nmi` paths 404.** Best free leading indicator (new orders lead
output by 1-2 quarters). NDC mirrors it but 403s non-browser agents.

**NCCC 信用卡消費** — the best free read on consumer demand, and far larger than
previously recorded: **~2,300 static CSVs in 15 schemas**, monthly 201401→202604,
UTF-8-BOM, no key. Go direct to `www.nccc.com.tw/dataDownload/{維度}/{檔名}.CSV`
rather than through data.gov.tw. Full URL grammar, three code tables (地區/業別/維度)
and all 15 schemas are in `schemas.md` §6. The load-bearing traps:
- **`BANK_*` (發卡端, 38 issuers, cardholder attributes) and `NCCC_*` (收單/處理端,
  includes UnionPay/DFS/debit) are different populations — never add them.**
- **`Top10ForeignCardConsumption*` is OUTBOUND** (國人在海外刷卡), despite the name.
  Real inbound lives in `Foreign/Location|Location EC|Industry`. Magnitude proof:
  202604 Taipei-only Top10 = NT$13.87bn vs national inbound NT$8.01bn.
- **「跨境」(ICR) is a currency definition, not a geographic one** — "帳單原始幣別
  不為新臺幣". Cross-border e-commerce and DCC transactions billed in Taiwan count in;
  overseas swipes billed in TWD count out. It is not "spending while abroad".
- **「跨縣市」(DCR) is a postcode comparison**, so online orders (merchant registered
  in Taipei) contaminate it heavily — a poor proxy for travel/commuting spend.
- Industry codes mislead: **`LG`(住) includes 裝潢及電器**, **`EE`(文教康樂)
  includes 醫療及保健**.
- **產業別 × 跨境/跨縣市/國別 crosstabs do not exist** (15 combinations tested, all
  404). "How much clothing did Taipei residents buy in Japan" is unanswerable from
  open data — that needs MCC-level data from an issuer or NCCC directly.
- `ICR`/`DCR`/`Country`/`Billing Address` have counties but **no TWN total**;
  `EC`/`Foreign/Industry`/`NCCC Open Data/Industry` have TWN but **no counties**.
- EC series break at 2023-09 (繳費稅平台 folded in); `Billing Address` starts 202008.
Not 100% of card volume — use for trend and mix, not absolute size.

**PCC 政府採購** — `pcc-api.openfun.app/api/searchbytitle?query=…&page=1`,
same-day freshness (the official XML at `web.pcc.gov.tw` lags ~2 months).
Volunteer-run, no SLA, attribution required; `total_records: 10000` looks like a
cap, not a true count. Keep the official XML as a durable fallback.

**GCIS 公司登記** — `data.gcis.nat.gov.tw/od/data/api/{uuid}?$format=json&$filter=Business_Accounting_NO eq {統編}`,
keyless. The entity-resolution spine — but registration data only, no revenue.
Updates are 不定期. Dates are **民國 7 碼 zero-padded** (`0760221`), which must be
converted before joining fbfh's 西元 8 碼.
- The authoritative uuid list is `data.gcis.nat.gov.tw/resources/swagger/swagger.json`
  (16 APIs, with each one's required params and `$filter` regex). **Do not use the
  uuids shown on `/od/datacategory`** — those are internal `oid`s and every one
  returns `此API不存在`.
- **Correction (verified 2026-07): `Company_Name like` on a 統編-type API does NOT
  return 400.** It returns **HTTP 200 with an empty body** — silently
  indistinguishable from "no such company". To query by name use the dedicated
  endpoint `6BBA2268-1367-4B42-9CCA-BC17499EBE8C` (公司登記關鍵字查詢), which also
  requires `Company_Status`; its `like` is a substring match (查「台積電」returns
  台積電機/台積電梯 but **not** TSMC itself).
- Every error is HTTP 200 — missing `$filter` returns plain text
  `$filter參數有誤`. Validate that the body parses as JSON.
- `$top` caps at 1000, `$skip` at 500000 — no full dump of all ~1.6M companies.

## Known gaps

Not published as open data at all: **PPI/躉售物價** (retired).

**加班工時 — the earlier "annual only" note was wrong and the source is still
open.** Verified 2026-07: MOL's 860 datasets contain **no working-hours series at
any frequency** (a full title sweep for 工時/時數/工作時間 returned 7 hits, all
unrelated). The series belongs to DGBAS 受僱員工薪資與生產力統計 (monthly), which
this sweep could not retrieve — `www.dgbas.gov.tw/public/data/open/...csv` is
WAF-403, `winsta.dgbas.gov.tw/winsta/` 404s, and `nstatdb` returns the HTML query
UI rather than data. It is a component of the NDC leading indicator, which is why
`ndc_signal.py` shows it blank. **Needs a dedicated DGBAS sweep before anyone
relies on it.**

Decision-critical numbers that exist only outside open data — **台灣數位廣告市場量**
(DMA annual PDF), **線上新聞/內容付費率** (Reuters DNR Taiwan page), **文化內容
產業產值** (TAICCA/文化統計 PDFs) — are now verified with URLs, retrieval methods,
pitfalls and dated snapshot numbers in `external-sources.md`. Any advertising-
funded or subscription-media case needs them; nothing API-able substitutes.

**國貿署 貿易統計 FSC** — country × HS-code × month trade values, 38 years
back, latest month ~M+1.5 (verified to 2026/05). The one programmatic source
for「哪個市場買什麼」finer than the customs bulk CSV. Verified 2026-07:
- Host: `publicinfo.trade.gov.tw/cuswebo/` (**`cuswebo.trade.gov.tw` fails DNS**).
- Flow: `GET /cuswebo/FSC3000C?table=FSC3010F` for the session cookie, then
  `POST /cuswebo/FSC3010F/FSC3010P` with `rdoIE_CODE=E|I, rdoMON=1|2 (年|月),
  ddlYearS/E, ddlMonS/E, rdoCAC=6, ddlCNTRY={ISO2}, txtHS_CODE_S/E,
  rdoReportCode2=All`. Response is an HTML table — parse it yourself.
- **The captcha is front-end-only**: `/FunVerification/ValidateCode` is a
  separate AJAX call the server never checks on FSC3010P. Post straight through.
- The `Tview` XLS/ODF download 302s away — don't rely on it.
- Sibling tables: FSC3020F 按貨品, FSC3030F 國×貨品歷年, FSC3040F 國家名次,
  FSC3080I 國家代號對照.
- **`rdoUnit` is what the server reads, not `FrdoUnit`.** The visible 金額/重量/數量
  radio is named `FrdoUnit` and is ignored; setting it alone returns USD figures
  silently labelled as kg. `rdoUnit=1|2|3` = 美元/公斤/數量; `rdoUnit=0` returns empty.
- **HS codes auto-right-pad.** `220830`, `22083000` and `2208300000` return
  byte-identical results, so a 6-digit query is the sum of every 11-digit CCC
  beneath it — you never need the full CCC code.
- Missing any one form field → **302 to `Static/Error.html`**, not 4xx. Send
  `ddlCONTINENTAL` and `ddlAREA` even when unused.
- Column 2 of the response is an **auto-generated prior-period baseline**, not your
  query window. Don't mistake it for the current period.
- **FSC3020F (按貨品排名) cannot be driven programmatically** — every parameter
  combination 302s. To enumerate sub-codes, loop FSC3010F per HS code instead.
  FSC3020F also only reaches back to 2015 vs FSC3010F's 1989.
- **FSC3080I is the one endpoint that returns JSON**, not HTML:
  `POST /cuswebo/FSC3080I/GetFSC3080I_Form3` (empty body) → 274 countries with
  `{coll, NO, CNAME, ENAME}`. `_Form1` 302s.
- **This closes the 烈酒 gap.** HS `220830` (威士忌) monthly imports, 1989→2026, by
  country, with kg alongside USD so unit price is derivable. Verified: 2023 peak
  US$722.8M → 2024 US$600.9M (−16.9%) → 2025 US$487.5M (−18.9%), 2026H1 −10.6%.
  Still import-side, so destocking vs end-demand remains unresolved — but three
  consecutive years and −32.6% off peak is hard to explain by inventory alone.

**fbfh 出進口廠商名錄** — `fbfh.trade.gov.tw/opendata/companyData.csv`
(data.gov.tw/dataset/79641 302s here). 103 MB, ~373k rows, UTF-8 BOM, daily.
統編, names/addresses, 進口資格/出口資格 flags. **A directory, not statistics**
— no counts by product/market; 實績級距 is per-company web lookup only;
representative names are masked (賴O佳). Entity-resolution companion to GCIS.

**投審司 對外投資統計** — the datasets exist on data.gov.tw (32520 分區 / 32521
分業 / 32522 分區分業 monthly, plus 32523-25 對中國大陸 variants; inbound 32514-18)
but every resource URL points at `wHandMenuFile.ashx` — the CF-403 handler
already in the Dead list — and `moeaic.gov.tw` itself times out from scripts.
**Programmatically dead as of 2026-07**; browser-only. If outward-investment
numbers become load-bearing, fetch by hand or via an interactive browser session.

## Dead — do not retry

`statdb.dgbas.gov.tw` (decommissioned 2021) · `dmz26.moea.gov.tw` (no DNS) ·
`cpx.cbc.gov.tw/api/OpenData/DataSet` (200, empty) · `rate.bot.com.tw` (Akamai) ·
`mops.twse.com.tw/mops/web/t21sc03` (302→404) · `wHandMenuFile.ashx` (CF-403) ·
`index.ndc.gov.tw` (CF-403) ·
data.gov.tw `/api/front/dataset/search` and `/api/v1/rest/dataset?q=` (never existed) ·
`portal.sw.nat.gov.tw/APGA/GA30` (server-side captcha, not replayable — use the
FSC tables instead, same customs source) · `data.customs.gov.tw` (no DNS) ·
`cuswebo.trade.gov.tw` (no DNS — the app lives at `publicinfo.trade.gov.tw`) ·
customs `data/24152/csv.csv` 三角貿易 (downloads fine but frozen at 民國 103-106)

Note `web02.mof.gov.tw/njswww` graduated OFF this list: the query UI has no API,
but its CSV export URLs are stable and wrapped (`mof_industry.py`).
