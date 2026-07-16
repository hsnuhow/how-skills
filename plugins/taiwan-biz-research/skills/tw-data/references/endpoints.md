# Verified Taiwan data endpoints

Every row below was fetched successfully while building this skill. All are free
and keyless unless noted. Wrapped = a script in `../scripts/` already handles it;
otherwise use `twdata/_fetch.py` directly — it absorbs the pitfalls.

## Wrapped

| Signal | Source | Depth | Script |
|---|---|---|---|
| 景氣對策信號 + 領先/同時/落後指標 + 構成項目 | data.gov.tw `6099` → `ws.ndc.gov.tw` ZIP | **1984→** monthly | `ndc_signal.py` |
| 平均每戶消費支出按區域別 | data.gov.tw `9420` (DGBAS CSV) | 1998→ annual | `household.py --spend` |
| 各縣市別平均每戶可支配所得 | data.gov.tw `9415` | 1998→ annual | `household.py --spend` |
| 家庭消費支出結構按消費型態 | data.gov.tw `6588` | **1976→** annual | `household.py --mix` |
| 戶數五等分位之可支配所得/消費支出/儲蓄 | data.gov.tw `6565` | **1976→** annual | `household.py --quintile` |
| 縣市戶數 (村里級彙總) | `ris.gov.tw/rs-opendata/api/v1/datastore/ODRP019/{ROC}?page=N` | 107→ annual | `household.py` |

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
Mixes ROC and AD dates across endpoints.

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
- 工業生產指數 (`16366`, 1.19 MB, →1982-01)
- 批發零售及餐飲業營業額指數 (`16365`, 870 KB) — released 23rd-26th of the next month
- 外銷訂單: 電子產品 (`16362`) / 資通訊 (`16361`), →1984-01

**CBC** — `www.cbc.gov.tw/public/data/OpenData/…` (URL-encode the Chinese dirs).
**The one agency using AD dates.** Its OpenAPI is a trap (200 + empty body).
- M1A/M1B/M2: `經研處/EF15M01.csv` — 1987M05→
- 匯率 NTD/USD daily: `外匯局/FTDOpenData015.csv` — 4,607 rows, 20080102→
- 利率: `業務局/xl/XOpen3.csv` — 2003→

**MOF** — 進出口貿易 `opendata.customs.gov.tw/data/6053/csv.csv` (CSV only;
`json.json` 404s). 賦稅統計 `eip.fia.gov.tw/OAI/api/{resource}?limit=1&offset=0`
— **both `limit` and `offset` are required**, paths case-sensitive.

**MOL** — `apiservice.mol.gov.tw/OdService/rest/dataset` → 860 dataset ids;
`/datastore/{id}` for data. `?modified=yyyy-MM-dd` for incremental sync.

**CIER PMI/NMI** — free monthly Excel with full history at
`cier.edu.tw/en/eco_cat/pmi-en/` and `/nmi-en/`. **Resolve from the page — the
short `/pmi` and `/nmi` paths 404.** Best free leading indicator (new orders lead
output by 1-2 quarters). NDC mirrors it but 403s non-browser agents.

**NCCC 信用卡消費** — data.gov.tw, monthly CSV, real transactions by 縣市 ×
產業 × 性別 × 職業. Best free consumer-demand granularity: `62945` (EC by
industry), `38329` (occupation × county). Not 100% of card volume — use for
trend and mix, not absolute size.

**PCC 政府採購** — `pcc-api.openfun.app/api/searchbytitle?query=…&page=1`,
same-day freshness (the official XML at `web.pcc.gov.tw` lags ~2 months).
Volunteer-run, no SLA, attribution required; `total_records: 10000` looks like a
cap, not a true count. Keep the official XML as a durable fallback.

**GCIS 公司登記** — `data.gcis.nat.gov.tw/od/data/api/{uuid}?$format=json&$filter=Business_Accounting_NO eq {統編}`,
keyless. Filter by 統編, not by name (`Company_Name like` returns 400). The
entity-resolution spine — but registration data only, no revenue. Updates are
不定期.

## Known gaps

Not published as open data at all: **PPI/躉售物價** (retired), **monthly 加班工時**
(annual only — and it's a component of the NDC leading indicator, which is why
`ndc_signal.py` shows it blank).

## Dead — do not retry

`statdb.dgbas.gov.tw` (decommissioned 2021) · `dmz26.moea.gov.tw` (no DNS) ·
`cpx.cbc.gov.tw/api/OpenData/DataSet` (200, empty) · `rate.bot.com.tw` (Akamai) ·
`mops.twse.com.tw/mops/web/t21sc03` (302→404) · `wHandMenuFile.ashx` (CF-403) ·
`web02.mof.gov.tw/njswww` (no API, flaky) · `index.ndc.gov.tw` (CF-403) ·
data.gov.tw `/api/front/dataset/search` and `/api/v1/rest/dataset?q=` (never existed)
