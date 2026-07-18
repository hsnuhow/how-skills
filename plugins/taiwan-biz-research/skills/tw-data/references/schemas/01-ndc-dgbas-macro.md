以下是可直接貼用的成品內容。

---

### NDC 景氣對策信號（`ndc_signal.py` / data.gov.tw dataset 6099）

取得路徑：`https://data.gov.tw/api/v2/rest/dataset/6099` → 解析出 ZIP 下載網址（`https://ws.ndc.gov.tw/Download.ashx?u=<base64>`）→ 解壓。ZIP 內含 5 個資料 CSV + 5 個 schema CSV + `manifest.csv`。

| 項目 | 值 |
|---|---|
| 編碼 | 內容 UTF-8-BOM（`utf-8-sig`）；**ZIP entry 檔名是 Big5**，未設 UTF-8 flag |
| 日期格式 | AD 六位數字 `YYYYMM`（欄名 `Date`，如 `202605`），非民國 |
| 涵蓋期間 | `198201` → **`202605`**（實測，2026-07-18 抓取） |
| 列數 | 每個資料 CSV 皆 533 列 |
| 燈號分數 | 9–45 分；藍 9-16 / 黃藍 17-22 / 綠 23-31 / 黃紅 32-37 / 紅 38-45 |

ZIP 內資料檔與欄位：

| 檔名 | 欄位 |
|---|---|
| `景氣指標與燈號.csv` | `Date`, `領先指標綜合指數`, `領先指標不含趨勢指數`, `同時指標綜合指數`, `同時指標不含趨勢指數`, `落後指標綜合指數`, `落後指標不含趨勢指數`, `景氣對策信號綜合分數`, `景氣對策信號` |
| `景氣對策信號構成項目.csv` | `Date`, `貨幣總計數M1B(百萬元)`, `股價指數(Index1966=100)`, `工業生產指數(Index2021=100)`, `工業及服務業加班工時(小時)`, `海關出口值(十億元)`, `機械及電機設備進口值(十億元)`, `製造業銷售量指數(Index2021=100)`, `批發、零售及餐飲業營業額(十億元)` |
| `領先指標構成項目.csv` | `Date`, `外銷訂單動向指數(以家數計)`, `貨幣總計數M1B(百萬元)`, `股價指數(Index1966=100)`, `工業及服務業受僱員工淨進入率(%)`, `建築物開工樓地板面積(住宅類住宅、商業辦公、工業倉儲)(千平方公尺)`, `名目半導體設備進口(新臺幣百萬元)` |
| `同時指標構成項目.csv` | `Date`, `工業生產指數(Index2021=100)`, `電力(企業)總用電量(十億度)`, `製造業銷售量指數(Index2021=100)`, `批發、零售及餐飲業營業額(十億元)`, `工業及服務業加班工時(小時)`, `海關出口值(十億元)`, `機械及電機設備進口值(十億元)` |
| `落後指標構成項目.csv` | `Date`, `失業率(%)`, `製造業單位產出勞動成本指數(2021=100)`, `五大銀行新承做放款平均利率(年息百分比)`, `全體金融機構放款與投資(10億元)`, `製造業存貨價值(千元)` |

真實範例（`景氣指標與燈號.csv` 最後一列）：

```
Date=202605, 領先指標綜合指數=132.2251004, 領先指標不含趨勢指數=103.8054711,
同時指標綜合指數=137.7038406, 同時指標不含趨勢指數=108.105946,
落後指標綜合指數=131.0716816, 落後指標不含趨勢指數=102.8992952,
景氣對策信號綜合分數=39, 景氣對策信號=紅
```

`--history 6` 實測輸出（2026-05 為最新）：2025-12 38分紅、2026-01 39分紅、2026-02 41分紅、2026-03 39分紅、2026-04 40分紅、2026-05 39分紅。

**坑**
- **`--components` 這個 flag 不存在。** 實際只有 `-h/--help`、`--history N`、`--json` 三個。打 `--components` 會得到 `error: unrecognized arguments: --components`。構成項目是**預設就會印**的，不需要旗標。
- ZIP entry 檔名以 Big5 編碼且未設 UTF-8 flag，Python `zipfile` 與 `unzip` 都會用 cp437 解出亂碼，必須 `name.encode("cp437").decode("big5")` 救回。檔案**內容**是 utf-8-sig，只有檔名要處理。
- 下載網址內嵌 base64 blob，每次重新上傳就會變；必須每次 resolve dataset id，不可寫死。
- 1984 年以前的燈號欄位是字面上的 `-`（不是空字串），`景氣對策信號` 欄還帶尾端空白（`'黃藍 '`），直接 group by 原始值會把同一類別拆成兩類。
- 構成項目最新月份常有 2 項空白（`工業及服務業加班工時`、`製造業銷售量指數`），屬正常發布時差，不是抓取失敗。落後指標的 `製造業單位產出勞動成本指數`、`製造業存貨價值` 在最新月同樣為空。
- data.gov.tw 對 Python 預設 UA 回 403，必須帶瀏覽器 UA。

---

### DGBAS 失業率 — `mp0101a07.xml`

`https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230038/mp0101a07.xml`

| 項目 | 值 |
|---|---|
| HTTP | 200，1,019,272 bytes，0.61s |
| 編碼 | UTF-8（**無 BOM**），CRLF 換行，宣告 `<?xml version='1.0' encoding='utf-8'?>` |
| 結構 | flat：`<DataCollection>` → 630 個 `<失業率>` → 22 個子元素 |
| 日期格式 | AD。年度列 `1978`，月列 `1978M01`（含 `M`） |
| 單位 | 全部百分比（%），tag 名以 `_百分比` 結尾 |
| 涵蓋期間 | `1978` / `1978M01` → **`2026M05`** |
| 列數 | 630 筆記錄（581 月 + 49 年度） |

完整 tag 清單（每筆記錄）：
`年月別_Year_and_month`, `總計_Total_百分比`, `男_Male_百分比`, `女_Female_百分比`, `age_15-19_百分比`, `age_20-24_百分比`, `age_25-29_百分比`, `age_30-34_百分比`, `age_35-39_百分比`, `age_40-44_百分比`, `age_45-49_百分比`, `age_50-54_百分比`, `age_55-59_百分比`, `age_60-64_百分比`, `age_65_over_百分比`, `國中及以下_Junior_high_and_below_百分比`, `國小及以下_Primary_school_and_below_百分比`, `國中_Junior_high_百分比`, `高級中等_高中_高職__Senior_high_school__regular_and_vocational__百分比`, `大專及以上_Junior_college_and_above_百分比`, `專科_Junior_college_百分比`, `大學及以上_University_and_above_百分比`

真實最後一筆：

```xml
  <失業率>
    <年月別_Year_and_month>2026M05</年月別_Year_and_month>
    <總計_Total_百分比>3.27</總計_Total_百分比>
    <男_Male_百分比>3.32</男_Male_百分比>
    <女_Female_百分比>3.2</女_Female_百分比>
    <age_15-19_百分比>9.59</age_15-19_百分比>
    ...
    <大學及以上_University_and_above_百分比>3.97</大學及以上_University_and_above_百分比>
  </失業率>
```

**坑**
- 年度列與月列**交錯在同一份檔案**（`1978` 緊接 `1978M01`）。不過濾就會把年平均值混進月序列。判別式：期別結尾有 `M\d{2}` 才是月資料。
- tag 名含連字號（`age_15-19_百分比`）與雙底線（`高級中等_高中_高職__Senior_high...`），不是合法 Python 識別字，只能用字串取值。
- 數值未補零：`3.2` 而非 `3.20`。
- 此檔為 flat schema，`dgbas_macro.py --items` **不適用**，會直接 `SystemExit: --items only applies to sdmx files; unemployment is flat`。

---

### DGBAS 勞動力參與率 — `mp0101a06.xml`

`https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230038/mp0101a06.xml`

| 項目 | 值 |
|---|---|
| HTTP | 200，1,043,230 bytes，0.40s |
| 編碼 | UTF-8 無 BOM，CRLF |
| 結構 | flat：`<DataCollection>` → 630 個 `<勞動力參與率>` → 22 個子元素 |
| 日期格式 | AD，`1978` / `1978M01` |
| 單位 | 百分比（%） |
| 涵蓋期間 | `1978M01` → **`2026M05`** |
| 列數 | 630 筆（581 月 + 49 年度） |

欄位結構與失業率檔**完全相同**（22 個 tag，逐字一致），只有 record tag 名不同。真實最後一筆：

```xml
  <勞動力參與率>
    <年月別_Year_and_month>2026M05</年月別_Year_and_month>
    <總計_Total_百分比>59.5</總計_Total_百分比>
    <男_Male_百分比>67.15</男_Male_百分比>
    <女_Female_百分比>52.33</女_Female_百分比>
    ...
  </勞動力參與率>
```

**坑**：與失業率檔同源同結構，可共用同一支 parser；唯一差異是 record tag。年度／月份交錯問題相同。

---

### DGBAS 每人每月經常性薪資 — `mp05002.xml`

`https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230037/mp05002.xml`

| 項目 | 值 |
|---|---|
| HTTP | 200，1,948,859 bytes，0.94s |
| 編碼 | UTF-8 無 BOM，CRLF |
| 結構 | flat：`<DataCollection>` → 604 個 `<每人每月經常性薪資>` → 23 個子元素 |
| 日期格式 | AD，**六位純數字 `202605`（沒有 `M`）**，與人力統計檔不同 |
| 單位 | **新臺幣元**（不是千元），tag 名以 `_金額_新臺幣元` 結尾 |
| 涵蓋期間 | `1980` / `198001` → **`202605Ⓟ`** |
| 列數 | 604 筆（557 月 + 47 年度） |

完整 tag 清單：
`年月別_Year_and_month`, `工業及服務業__Industry_and_services_金額_新臺幣元`, `男性_Male_金額_新臺幣元`, `女性_Female_金額_新臺幣元`, `工業_Industrial_金額_新臺幣元`, `礦業及土石採取業_Mining_and_quarrying_金額_新臺幣元`, `製造業_Manufacturing_金額_新臺幣元`, `電力及燃氣供應業_Electricity_and_gas_supply_金額_新臺幣元`, `用水供應及污染整治業_Water_supply_and_remediation_activities_金額_新臺幣元`, `營建工程業_Construction_金額_新臺幣元`, `服務業_Services_金額_新臺幣元`, `批發及零售業_Wholesale_and_retail_trade_金額_新臺幣元`, `運輸及倉儲業_Transportation_and_storage_金額_新臺幣元`, `住宿及餐飲業_Accommodation_and_food_service_activities_金額_新臺幣元`, `出版影音及資通訊業_Information_and_communication_金額_新臺幣元`, `金融及保險業_Financial_and_insurance_activities_金額_新臺幣元`, `不動產業_Real_estate_activities_金額_新臺幣元`, `專業科學及技術服務業_Professional_scientific_and_technical_activities_金額_新臺幣元`, `支援服務業_Support_service_activities_金額_新臺幣元`, `教育業_Education_金額_新臺幣元`, `醫療保健及社會工作服務業_Human_health_and_social_work_activities_金額_新臺幣元`, `藝術_娛樂及休閒服務業_Arts_entertainment_and_recreation_金額_新臺幣元`, `其他服務業_Other_service_activities_金額_新臺幣元`

真實最後一筆（節錄）：

```xml
  <每人每月經常性薪資>
    <年月別_Year_and_month>202605Ⓟ</年月別_Year_and_month>
    <工業及服務業__Industry_and_services_金額_新臺幣元>49216</工業及服務業__Industry_and_services_金額_新臺幣元>
    <男性_Male_金額_新臺幣元>52420</男性_Male_金額_新臺幣元>
    <女性_Female_金額_新臺幣元>45583</女性_Female_金額_新臺幣元>
    <製造業_Manufacturing_金額_新臺幣元>47190</製造業_Manufacturing_金額_新臺幣元>
    <金融及保險業_Financial_and_insurance_activities_金額_新臺幣元>74703</金融及保險業_Financial_and_insurance_activities_金額_新臺幣元>
    <住宿及餐飲業_Accommodation_and_food_service_activities_金額_新臺幣元>34918</住宿及餐飲業_Accommodation_and_food_service_activities_金額_新臺幣元>
    ...
  </每人每月經常性薪資>
```

**坑**
- **期別帶狀態記號**：`202604Ⓡ`（修正值 revised）、`202605Ⓟ`（初步值 preliminary）。這是 U+24C7 / U+24C5 圈字元，直接拿去做期別 join 會靜默對不上，必須先剝掉。可能出現的記號集合：`Ⓡ Ⓟ Ⓞ *`。
- **日期格式與人力統計檔不一致**：這裡是 `202605`，失業率檔是 `2026M05`。同一機關同一批 XML，兩種格式，跨檔 join 要先正規化。
- 早期年份的部分行業是字面 `-`（如 1980 年 `教育業_Education_金額_新臺幣元` 為 `-`），不是空字串也不是 0。
- 單位是**元**，不是千元；不要因為政府統計常用千元就自行乘除。
- `工業及服務業` 的 tag 名有**兩個連續底線**（`工業及服務業__Industry_and_services_金額_新臺幣元`），前綴比對時容易寫錯。

---

### DGBAS 每人每月總薪資 — `mp05001.xml`

`https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230037/mp05001.xml`

| 項目 | 值 |
|---|---|
| HTTP | 200，1,942,089 bytes，0.60s |
| 編碼 | UTF-8 無 BOM，CRLF |
| 結構 | flat：`<DataCollection>` → 604 個 `<每人每月總薪資>` → 23 個子元素 |
| 日期格式 | AD 六位 `202605`，帶 `Ⓡ`/`Ⓟ` 記號 |
| 單位 | 新臺幣元 |
| 涵蓋期間 | `198001` → **`202605Ⓟ`** |
| 列數 | 604 筆（557 月 + 47 年度） |

欄位與 `mp05002.xml` **完全相同**（23 個 tag 逐字一致），只有 record tag 為 `每人每月總薪資`。真實最後一筆（節錄）：

```xml
  <每人每月總薪資>
    <年月別_Year_and_month>202605Ⓟ</年月別_Year_and_month>
    <工業及服務業__Industry_and_services_金額_新臺幣元>62579</工業及服務業__Industry_and_services_金額_新臺幣元>
    <男性_Male_金額_新臺幣元>69011</男性_Male_金額_新臺幣元>
    <女性_Female_金額_新臺幣元>55287</女性_Female_金額_新臺幣元>
    ...
  </每人每月總薪資>
```

**坑**
- 總薪資含獎金，月間波動極大：實測 `202604` 為 57,448 元、`202605` 跳到 62,579 元（+8.9%），這是年中獎金效應不是資料錯誤。做趨勢分析請用經常性薪資（`mp05002`）。
- 其餘坑同 `mp05002.xml`（狀態記號、年月交錯、`-` 缺值、單位為元）。

---

### DGBAS 國民所得統計（季）— `na8101a1q.xml`

`https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230514/na8101a1q.xml`

| 項目 | 值 |
|---|---|
| HTTP | 200，1,272,941 bytes，0.40s |
| 編碼 | UTF-8 無 BOM，CRLF，宣告 `<?xml version="1.0" encoding="utf-8" ?>`（雙引號，與 flat 檔的單引號不同） |
| 結構 | SDMX-like long format |
| 日期格式 | `TIME_PERIOD` = `1961Q1` … `2026Q1`（AD + 季） |
| 單位 | 隨 Item 而異，寫在 Item 名稱括號內 |
| 涵蓋期間 | `1961Q1` → **`2026Q1`**（261 個期別）；經濟成長率有值者 `1962Q1` → `2026Q1` |
| 列數 | 7,830 個 `<Obs>`（15 items × 261 periods × 2 types） |

根元素與前 3 行原文：

```xml
<?xml version="1.0" encoding="utf-8" ?>
<DataSet 
 Sender_NAME="行政院主計總處" 
 Tab_NAME="國民所得統計常用資料-季"> 
<Obs><Item>期中人口(人)</Item><TIME_PERIOD>1961Q1</TIME_PERIOD><FREQ>Q</FREQ><TYPE>原始值</TYPE>
<Item_VALUE>10895610</Item_VALUE></Obs>
```

`<Obs>` 子元素：`Item`, `TIME_PERIOD`, `FREQ`（僅 `Q`）, `TYPE`（`原始值` / `年增率(%)`）, `Item_VALUE`。

15 個 Item（含單位）：
`期中人口(人)`, `平均匯率(元/美元)`, `經濟成長率(%)`, `國內生產毛額GDP(名目值，百萬元)`, `國內生產毛額GDP(名目值，百萬美元)`, `平均每人GDP(名目值，元)`, `平均每人GDP(名目值，美元)`, `國民所得毛額GNI(名目值，百萬元)`, `國民所得毛額GNI(名目值，百萬美元)`, `平均每人GNI(名目值，元)`, `平均每人GNI(名目值，美元)`, `國民所得(名目值，百萬元)`, `國民所得(名目值，百萬美元)`, `平均每人所得(名目值，元)`, `平均每人所得(名目值，美元)`

實測最新值：`經濟成長率(%)` `2026Q1` = **14.55**。

**坑**
- 每個期別出現**兩次**（`原始值` 一次、`年增率(%)` 一次），不過濾 `TYPE` 會得到雙倍列數與混雜語意的序列。
- **`經濟成長率(%)` 的 `年增率(%)` 全部為空**（261 筆皆空 `<Item_VALUE></Item_VALUE>`）——它本身已是成長率，再取年增率無意義。取這個 item 時只能用 `TYPE=原始值`；寫成通用抓 `年增率` 的程式會拿到 0 筆並在取 `[-1]` 時 IndexError。
- 空值是 `<Item_VALUE></Item_VALUE>`（元素存在但無 text，`findtext` 回傳 `''` 而非 `None`）。1961Q1–1961Q4 的年增率因無前期基準而全空。
- 單位混在 Item 名稱字串裡（`百萬元` vs `百萬美元` vs `元`），只看 `Item_VALUE` 無法判斷幣別，必須解析 Item 名稱。
- `<Obs>` 內容跨兩行（`Item_VALUE` 另起一行），逐行 regex 會失效，請用 XML parser。
- **`dgbas_macro.py --annual` 對此檔無效**：季檔本來就只有季別，該旗標只是關掉 sub-annual 過濾，不會產出年度值。

---

### DGBAS 消費者物價基本分類指數 — `pr0101a1m.xml`

`https://ws.dgbas.gov.tw/001/Upload/461/relfile/11525/230555/pr0101a1m.xml`

| 項目 | 值 |
|---|---|
| HTTP | 200，**15,714,987 bytes**（15.0 MiB），3.96s |
| 編碼 | UTF-8 無 BOM，CRLF |
| 結構 | SDMX-like long format，同 GDP 檔 |
| 日期格式 | `TIME_PERIOD` = `1981M01` … `2026M06`（AD + `M` + 兩位月） |
| 單位 | 指數（**基期：民國110年=100**），另有 `年增率(%)` |
| 涵蓋期間 | `1981M01` → **`2026M06`**（546 個月） |
| 列數 | 88,452 個 `<Obs>`（81 items × 546 periods × 2 types） |

根元素與前 3 行原文：

```xml
<?xml version="1.0" encoding="utf-8" ?>
<DataSet 
 Sender_NAME="行政院主計總處" 
 Tab_NAME="消費者物價基本分類指數"> 
<Obs><Item>總指數(指數基期：民國110年=100)</Item><TIME_PERIOD>1981M01</TIME_PERIOD><FREQ>M</FREQ><TYPE>原始值</TYPE>
<Item_VALUE>52.95</Item_VALUE></Obs>
```

實測最新值：`總指數` `2026M06` 原始值 = **112.01**，年增率 = **2.6%**。

**`--cpi --items` 完整品項清單（81 項，全部帶 `(指數基期：民國110年=100)` 後綴，以下省略後綴）：**

| 層級 | 品項 |
|---|---|
| 總 | `總指數` |
| 一.食物類 | `一.食物類`；`1.穀類及其製品`（`(1)米類及其製品`、`(2)其他穀類及其製品`）；`2.肉類`（`(1)生鮮家畜`、`(2)生鮮家禽`）；`3.肉類製品`；`4.蛋類`；`5.水產品`；`6.加工水產品`；`7.蔬菜`（`(1)根菜`、`(2)莖菜`、`(3)葉菜`、`(4)果菜及其他`）；`8.加工蔬菜`；`9.水果`；`10.加工水果`；`11.乳類`；`12.食用油`；`13.調味品`；`14.酒`；`15.非酒精性飲料及材料`；`16.調理食品`；`17.外食費`；`18.其他食品` |
| 二.衣著類 | `二.衣著類`；`1.成衣`（`(1)男用衣著`、`(2)女用衣著`、`(3)兒童衣著及學生制服`）；`2.鞋類`；`3.衣著服務及配件` |
| 三.居住類 | `三.居住類`；`1.房租`；`2.住宅維修費`（`(1)維修材料`、`(2)維修服務`）；`3.家庭用品`（`(1)紡織品`、`(2)家具`、`(3)家庭耐久設備`、`(4)餐具及其他家用品`）；`4.家庭管理費用`；`5.水電燃氣`（`(1)燃氣`、`(2)水費`、`(3)電費`、`(4)公共附加費`） |
| 四.交通及通訊類 | `四.交通及通訊類`；`1.交通及通訊設備`（`(1)交通工具`、`(2)通訊設備`）；`2.油料費`；`3.交通服務及維修零件`（`(1)運輸費`、`(2)通訊費`、`(3)交通工具零件及維修費`、`(4)其他交通服務費`） |
| 五.醫藥保健類 | `五.醫藥保健類`；`1.醫療費用`；`2.藥品及保健食品`；`3.醫療保健器材` |
| 六.教養娛樂類 | `六.教養娛樂類`；`1.教養費用`（`(1)書報期刊`、`(2)學雜費`、`(3)補習及學習費`、`(4)教養設備及用具`）；`2.娛樂費用`（`(1)娛樂設備`、`(2)娛樂服務`） |
| 七.雜項類 | `七.雜項類`；`1.香菸及檳榔`；`2.美容及衛生用品`；`3.個人隨身用品`；`4.個人照顧服務費`；`5.理容服務費`；`6.其他` |

**坑**
- **`curl -r 0-200000` 沒有作用。** 伺服器忽略 Range 標頭，回 `HTTP 200` 並送出完整 15,714,987 bytes（實測 3.96s）。沒有 `206 Partial Content`。想省流量只能靠客戶端串流早停，不能靠 Range。所幸全檔下載本身很快，直接抓完整檔即可。
- **品項名稱內嵌基期，且主計總處每五年改基期一次**（現為民國110年=100）。用 `Item == "總指數"` 精確比對會在改基期當天靜默回傳 0 筆。必須用 `startswith("總指數")` 前綴比對。
- 品項名稱帶編號前綴與**全形括號層級**（`一.`、`1.`、`(1)`），三層混在同一個扁平 Item 欄位，沒有獨立的層級欄位——要建樹狀結構得自行解析編號樣式。
- 每期別出現兩次（`原始值` / `年增率(%)`），同 GDP 檔。`年增率` 在 1981 全年為空（無前期基準），`總指數` 年增率實際起點是 `1982M01`。
- 88,452 個 `<Obs>` 用 `ElementTree.fromstring` 全載約需數百 MB 記憶體峰值；只要單一品項時建議用 `iterparse` 串流。
- 注意 `TIME_PERIOD` 到 `2026M06`，比人力/薪資統計（`2026M05`）**多一期**。跨來源對齊時最新月會不一致。

---

### `dgbas_macro.py` 旗標總表

腳本路徑：`/Users/how/.claude/plugins/cache/how-skills/taiwan-biz-research/0.5.1/skills/tw-data/scripts/dgbas_macro.py`
共用抓取層：`/Users/how/.claude/plugins/cache/how-skills/taiwan-biz-research/0.5.1/skills/tw-data/scripts/twdata/_fetch.py`

| 旗標 | 說明 | schema | 預設欄位 | 單位 | 實測最新值（2026-07-18） |
|---|---|---|---|---|---|
| `--unemployment` | 失業率 `230038/mp0101a07.xml` | flat | `總計_Total_百分比` | % | `2026M05` = 3.27%（581 期，起 `1978M01`） |
| `--labour` | 勞動力參與率 `230038/mp0101a06.xml` | flat | `總計_Total_百分比` | % | `2026M05` = 59.50%（581 期，起 `1978M01`） |
| `--wage` | 經常性薪資 `230037/mp05002.xml` | flat | 第一個數值欄 | 元 | `202605` = 49,216 元（557 期，起 `198001`） |
| `--total-wage` | 總薪資 `230037/mp05001.xml` | flat | 第一個數值欄 | 元 | `202605` = 62,579 元（557 期，起 `198001`） |
| `--gdp` | 經濟成長率 `230514/na8101a1q.xml` | sdmx | `經濟成長率(%)` | % | `2026Q1` = 14.55%（257 期，起 `1962Q1`） |
| `--cpi` | 消費者物價指數 `230555/pr0101a1m.xml` | sdmx | `總指數` | 指數 | `2026M06` = 112.01（546 期，起 `1981M01`） |

修飾旗標（六個系列旗標互斥，必選其一）：

| 旗標 | 說明 |
|---|---|
| `--history N` | 顯示最近 N 期，預設 8 |
| `--annual` | 改取年度列而非月/季列 |
| `--items` | 列出 sdmx 檔內的所有序列名稱 |
| `--json` | 輸出 `{"series", "unit", "rows":[{"period","value"}]}` |

**坑**
- **`--items` 只支援 sdmx 檔**（`--gdp`、`--cpi`）。對 flat 檔會硬失敗：`--items only applies to sdmx files; unemployment is flat`。想看 flat 檔欄位只能自己讀 XML 第一筆記錄的子元素。
- **`--annual` 名不符實。** 它並非「改取年度列」，而只是關掉 sub-annual 過濾，導致年度列與月列**混在一起**回傳。實測 `--unemployment --annual --history 3` 顯示的仍是 `2026M03/04/05` 三個**月**，只是總期數從 581 膨脹到 629。要真正拿年度值必須自行反向過濾（挑出**沒有** `M\d{2}`/`Q[1-4]`/六位數字結尾的期別）。
- `--wage` / `--total-wage` 沒有指定欄位，程式取「每列第一個可轉數值的欄位」，實務上等於 `工業及服務業`（全體平均）。想要分行業（如製造業、金融保險業）必須自己 parse XML，CLI 無法指定。
- 旗標命名有底線→連字號轉換：`total_wage` → `--total-wage`。
- `ws.dgbas.gov.tw` **憑證鏈不完整**：leaf 由 "TWCA Secure SSL Certification Authority" 簽發，但伺服器不送該中介憑證（送的是無關的 ePKI/GRCA）。Python + certifi 無法建立信任路徑會直接拒絕；`_fetch.py` 偵測到 `SSLCertVerificationError` 會自動 fallback 到 `curl`（用 OS 信任庫，內含台灣政府 CA），驗證仍開啟。若環境沒有 `curl` 就會整組失敗。
- `_fetch.py` 的核心防禦：**HTTP 200 不代表拿到資料**。政府主機常以 200 回 HTML 錯誤頁、bot challenge、空 body 或只有表頭的檔案。所有 fetch 都驗 payload（`_NOT_DATA` 簽章比對 + `min_bytes=512` 門檻），不看狀態碼。
- 逾時設定 `TIMEOUT = 60` 秒。CPI 檔 15 MB 實測 3.96s，在額度內；但網路較差時 60s 可能不夠，這是唯一有逾時風險的端點。

---

### 本次無失敗端點

七個目標端點（1 個 data.gov.tw dataset + 6 個 DGBAS XML）全部 **HTTP 200 且回傳有效資料**，無逾時、無空 body、無 bot challenge。單檔最慢為 CPI 的 3.96s。

依指示未重試的已知死亡端點：`statdb.dgbas.gov.tw`、`cpx.cbc.gov.tw`、`index.ndc.gov.tw`。另據 `ndc_signal.py` 內註記，`index.ndc.gov.tw` 與 `www.ndc.gov.tw` 對非瀏覽器客戶端一律 Cloudflare 403，故 NDC 資料只能走 data.gov.tw 開放資料路徑。