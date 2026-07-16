# Taiwan government endpoint pitfalls

Everything here was hit while building this skill. `twdata/_fetch.py` handles
all of it — this file explains what it's defending against, for when you add a
new source and something behaves impossibly.

## 1. HTTP 200 that isn't data

The single biggest hazard. Verified in five independent places:

| Host | What 200 actually returns |
|---|---|
| `statdb.dgbas.gov.tw` | Big5 HTML notice: service ended 2021-04-13 |
| `cpx.cbc.gov.tw/api/OpenData/DataSet` | `content-length: 0` for every `set_id` |
| `rate.bot.com.tw/xrt/flcsv/0/day` | Akamai JS bot challenge |
| `mopsov.twse.com.tw/.../t21sc03_115_7_0.html` | 916 bytes — headers, zero rows: the month isn't published |
| `ris.gov.tw`, `eip.fia.gov.tw` | Error code inside a 200 body |

Never branch on `status_code == 200`. Validate the payload: byte size, content
signature, and `responseCode` where one exists.

The header-only case is the nastiest, because the file is *valid* — it just has
no rows. `fetch(min_bytes=...)` is the guard.

## 2. Dates are not uniform, even within one API

- **ROC (民國)**: TWSE (`1150715` = 2026-07-15), MOPS, MOEA (`11506` packed
  `YYYMM`), MOI (ROC year as a mandatory path segment), FIA.
- **AD (西元)**: CBC, NDC (`202605`), and the DGBAS **household surveys**.
- **Mixed inside one API**: TPEx — `/tpex_index` returns `20260701` (AD) while
  `/tpex_mainboard_quotes` returns `1150716` (ROC). Detect per value:
  **length 3/5/7 = ROC, 6/8 = AD** (`looks_roc()` / `roc_to_ad()`).
- **Mixed across DGBAS families**: 人力資源 `1978M01`, 薪資 `198001`, GDP `1961Q1`.

## 3. Encoding: the Big5 folklore is mostly wrong

Nearly everything verified is **UTF-8 with BOM** — use `utf-8-sig`; the BOM
breaks naive header parsing. `iconv -f big5` on a MOEA CSV produces garbage.

Big5 survives in exactly three places:
- **MOPS HTML**
- **NDC zip *filenames*** — the contents are utf-8-sig. `unzip` and Python both
  read the names as cp437 and mangle them; recover with
  `name.encode('cp437').decode('big5')` (`unzip()` does this).
- The statdb tombstone page.

## 4. URLs with Chinese characters

DGBAS serves files under literal Chinese filenames:

    https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/232214/011-平均每戶消費支出按區域別分.csv

`urllib` requires an ASCII request line and raises `UnicodeEncodeError`. curl
encodes silently, which is why a URL that works in a shell fails in Python.
`encode_url()` percent-encodes the path; already-encoded URLs pass through.

## 5. `ws.dgbas.gov.tw` serves a broken certificate chain

The leaf (`CN=www.dgbas.gov.tw`) is issued by **TWCA Secure SSL Certification
Authority** — but the server never sends that intermediate. It sends unrelated
ePKI Root G2 / GRCA G1 certificates instead. Python builds its path from certifi
and cannot complete the chain: `CERTIFICATE_VERIFY_FAILED`. curl succeeds
because the OS trust store carries the Taiwan government CAs.

This is the agency's misconfiguration, not ours. `_fetch.py` retries through
curl, which **still verifies** — it swaps trust stores rather than disabling the
check. Do not "fix" this with `ssl._create_unverified_context()`.

## 6. UA filtering

`Python-urllib/3.11` → **403**. curl → **200**, same URL. data.gov.tw and
several agency hosts filter on User-Agent. Always send a browser UA.

## 7. Response schemas change between years

MOI's `ODRP019`, same endpoint, same dataset:
- **ROC 114**: English keys — `site_id`, `household_ordinary_total`
- **ROC 113**: Chinese keys — `區域別`, `共同生活戶_戶數`

Read both spellings. Assume any long-running series may have done this.

MOI success is `responseCode: "OD-0101-S"`; `"OD-0102-S"` means 查無資料 (the
year isn't published — walk back a year, don't fail).

## 8. Missing-value markers and invisible whitespace

- "No data" is a literal `-`, not an empty cell (NDC pre-1984, CBC).
- **NDC's light column contains `'黃藍 '` with a trailing space.** Group on the
  raw value and one category silently splits into two.
- DGBAS marks revisions on the period itself: `202604Ⓡ`, `202605Ⓟ`. Left in
  place they break period joins. `strip_status()` removes them.

## 9. Metadata lies; blocked portals don't mean blocked data

- data.gov.tw `modifiedDate` reports 2024 for datasets serving 2026 data. Trust
  the file, not the metadata.
- **NDC**: `index.ndc.gov.tw` and `www.ndc.gov.tw` are Cloudflare-403 even with a
  browser UA — but `ws.ndc.gov.tw` (where the open data actually lives) is open.
- **MOEA**: the HTML portal is Cloudflare-403 while
  `service.moea.gov.tw/EE520/opendata/*.csv` is exempt. A 403 on the portal does
  not mean the data is unreachable.
- **NDC download URLs embed an opaque base64 blob that changes on re-upload.**
  Always `resolve_dataset(id)` fresh; never hardcode the URL.

## 10. Rate limits

TWSE bans at **>3 requests / 5 seconds** — real and enforced. No rate-limit
headers are published; ETag/Last-Modified are, so use conditional GETs.
