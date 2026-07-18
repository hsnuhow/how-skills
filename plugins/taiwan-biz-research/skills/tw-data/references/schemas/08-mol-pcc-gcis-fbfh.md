All four sources fetched live. Here is the catalogue section, ready to paste.

---

### MOL 勞動部開放資料 API (`apiservice.mol.gov.tw/OdService`)

**驗證時間**：2026-07-18。無金鑰、無 rate limit 觸發（12 併發 860 請求全數 200）。

#### 端點結構（實測，與傳聞版本不同）

| 端點 | 實測結果 |
|---|---|
| `GET /rest/dataset` | 回 JSON 字串陣列，**860 個 datasetId**。`["6153","5957","6058",…,"40596"]` |
| `GET /rest/dataset?modified=yyyy-MM-dd` | 增量可用。`modified=2026-07-17` → 33 個 id；`modified=2026-07-01` → 260 個 id。語意為「該日（含）之後有異動」 |
| `GET /rest/dataset/{datasetId}` | 單一資料集 metadata（含 `distribution[]`） |
| `GET /rest/datastore/{id}` | **`{id}` 必須是 resourceID，不是 datasetId**。傳 datasetId 一律回 `{"success":false,"error":{"message":"找不到指定的 resourceID 資料內容。","type":"ER0100"}}` 且 **HTTP 仍為 200** |
| `GET /download/{resourceID}` | 直接回檔案（CSV/JSON/XML 原檔，UTF-8 **含 BOM**） |

#### metadata schema（`/rest/dataset/6153` 真實回應）

```
categoryService, categoryDataset, datasetId, title, description, license, cost,
publisherOID ("2.16.886.101.20003.20063.20002|勞動部勞動力發展署"),
publisherContactName, publisherContactPhone, publisherContactEmail,
updateFrequency{regularupdate, unittime, frequency}, coverageStartedDate,
coverageEndedDate, publishedDate, modifiedDate ("2026-06-22 15:01:06"),
spatialCoverage, language, relatedUrl, keyword[], notes,
distribution[]{resourceID, resourceDescription, resourceField, resourceFormat,
               resourceCharacterEncoding, resourceModified,
               resourceDownloadUrl, resourceAmount, resourceNotes}
```

`resourceAmount` 實測**恆為 `"0"`**，不可當筆數用。

#### 對消費／薪資／就業研究有用的 dataset（實測 id 與 CSV resourceID）

| datasetId | 名稱 | 頻率 | CSV resourceID | 最新異動 |
|---|---|---|---|---|
| 6281 | 基本工資之制定與調整經過 | 不定 | `A17000000J-020050-MUA` | 2026-06-18 |
| 6647 | 初任人員薪資 | 年 | `A17000000J-020066-SCO` | 2026-04-24 |
| 41685 | 受僱員工人數、每人薪資-製造業(按職類別分) | 年 | `A17000000J-030089-jka` | 2026-06-30 |
| 41689 | 同上-批發及零售業 | 年 | `A17000000J-030093-F0a` | 2026-06-30 |
| 41691 | 同上-住宿及餐飲業 | 年 | `A17000000J-030095-O63` | 2026-06-30 |
| 41692 | 同上-出版影音及資通訊業 | 年 | （同系列） | 2026-06-30 |
| 41693 | 同上-金融及保險業 | 年 | （同系列） | 2026-06-30 |
| 41695 | 同上-專業、科學及技術服務業 | 年 | （同系列） | 2026-06-30 |
| 41698 | 同上-醫療保健及社會工作服務業 | 年 | （同系列） | 2026-06-30 |
| 6648 | 同上-礦業及土石採取業 | 年 | `A17000000J-020067-lEX` | 2026-06-30 |
| 33357 | 勞工保險平均投保薪資-按行業別 | 年 | `A17010000J-000095-fhJ` | 2026-02-24 |
| 33377 | 就業保險平均投保薪資-按行業別 | 年 | `A17010000J-000108-7fi` | 2026-02-24 |
| 46102 | 勞工退休金平均提繳工資-按行業別 | 年 | `A17000000J-030156-2d5` | 2026-06-09 |
| 46103 | 勞工退休金平均提繳工資-按年齡組別 | 年 | — | 2026-06-09 |
| 34057 | 勞工退休金提繳單位、提繳人數、提繳工資、提繳金額概況 | 年 | `A17010000J-000121-0bO` | 2026-06-08 |
| 146527 | 性別薪資差距 | 年 | `A17000000J-030266-pJX` | 2026-06-09 |
| 6258 / 45940 | 勞工保險投保薪資分級表 / 歷年分級表 | 不定 | `A17000000J-020014-Uy8` / `-030160-Bdr` | 2025-12-26 / 2026-06-09 |
| 119861 | 勞工保險投保人數-按地區別、投保薪資及性別 | 年 | `A17000000J-030232-2UH` | 2026-06-04 |
| 100999 | 勞工保險投保單位、人數及平均投保薪資原始統計 | 年 | `A17000000J-030212-2Au` | 2026-06-09 |
| 9819 | 勞工生活及就業狀況調查 | 年 | `A17000000J-020078-9Kq` | 2026-06-16 |
| 9565 | 15-29歲青年勞工就業狀況調查 | 年 | `A17000000J-020075-CiT` | 2026-06-11 |
| 9818 | 部分工時勞工就業實況調查 | 年 | `A17000000J-020077-kyQ` | 2026-06-12 |
| 40169 | 勞雇雙方協商減少工時概況（無薪假） | 年 | `A17000000J-020143-WB9` | 2026-06-10 |
| 44759 | 失業認定統計 | 月 | `A17000000J-030145-1au`（共 104 個 resource） | 2026-06-24 |
| 44062 | 台灣就業通網站職缺清單 | 日更 | `A17000000J-030144-MKw` | 2026-07-18 |
| 7884 | 勞動部近10年勞動統計調查 | 季 | `A17000000J-020064-CEu` | 2026-06-26 |

#### 真實資料範例（前 3 行）

**6281 基本工資**（`/download/A17000000J-020050-MUA`，38 列）
```
序號,年度,指示/發佈日期（民國）,內容/調整金額（新台幣）,實施日期（民國）
1,1930,19300101,政府批准國際勞工組織「設釐定最低工資機構公約」。,19300101
2,1936,19361223,國民政府公布最低工資法…,19360101
```
末列：`38,2023,20230914,"月薪27,470、時薪183",20240101`

**41685 製造業薪資**（2,890 資料列）
```
序號,年度,職類別,行業別,7月底受僱員工人數,7月經常性薪資（金額元）,113年1月至113年12月全年薪資所得（金額萬元）
1,2025,主管及監督人員,C000000000,265152,84598,151.5
2,2025,高階主管(總經理及總執行長),C000000000,23811,157798,298.9
3,2025,中階主管(經理),C000000000,86297,101419,182.1
```

**6647 初任人員薪資**（228 列）
```
"年度","教育程度別","特性別","占該教育程度別初任人員人數結構比（%）","薪資平均數（千元）"
114,"全體","全體",100,39
114,"全體","性別_男性",45.7,41
```

**146527 性別薪資差距**（14 列）
```
序號,統計項目別,細項,兩性差距（百分比）,備註
1,年度,100年,17.9,
2,年度,101年,17.3,
```

**44062 職缺清單**（欄名內嵌中文括號，恰 1,000 列）
```
"OCCU_DESC（職務名稱）","WK_TYPE（職務性質）","CJOB1_COUNT（職務大類別代碼）","CJOB_NAME1（職務大類別名稱）","CJOB2_COUNT（職務小類別代碼）","CJOB_NAME2（職務小類別名稱）","JOB_PERSON（雇用人數）","STOP_DATE（應徵截止日期）","JOB_DETAIL（工作內容）","CITYNAME（工作地點）","EXPERIENCE（工作經驗）","WKTIME（工作時間）","SALARYCD（核薪方式）","NT_L（薪資範圍下限）","NT_U（薪資範圍上限）","EDGRDESC（最低學歷要求）","URL_QUERY（職缺資料URL）","COMPNAME（公司名稱）","TRANDATE（職缺更新日期）"
"0717兼職清潔人員","全職","19","清潔／家事／托育(保母)","190101","大樓及辦公室清潔員","20","20260901",…,"時薪","250","250","不拘",…,"洋美環境維護股份有限公司","20260703"
```

#### 工時／加班工時：endpoints.md 的記載需要修正

實測結果：**MOL 開放資料 860 個 dataset 中，沒有任何一個包含受僱員工工時或加班工時**。全庫標題掃描 `工時|時數|工作時間|生產力|出勤` 只命中 7 筆，全部無關：

```
9818   部分工時勞工就業實況調查
143389 性別勞動統計之部分工時就業者人數
40169  勞雇雙方協商減少工時概況
152586 部分工時受僱勞工生活補貼
45942  部分工時被保險人各投保薪資投保人數
106661 TTQS輔導服務時數按地區分
18573  勞動力發展數位服務平台教材…觀看人次及時數累計
```

所以「月頻加班工時未公開、只有年頻」這句話對 MOL 而言是**錯的問法**：MOL 兩種頻率都沒有。「每人每月工時／加班工時」屬**主計總處「受僱員工薪資與生產力統計」**（月頻），不在 MOL。本輪未能完成 DGBAS 端點驗證（`www.dgbas.gov.tw/public/data/open/...csv` → 403；`winsta.dgbas.gov.tw/winsta/` → 404；`nstatdb.dgbas.gov.tw/dgbasall/webMain.aspx` 回 HTML 查詢頁而非資料）。**加班工時來源需另開一輪對 DGBAS 的專門盤點**，不要沿用舊記載。

#### 坑

- `/rest/datastore/{datasetId}` 不通，一定要先取 `distribution[].resourceID`。錯誤時 **HTTP 200 + `success:false`**，用 status code 判斷會靜默吃掉錯誤。
- 一個 dataset 常有數十個 resource（44759、6618 各 104 個；100999 有 36 個），一年／一版一個 resource。`distribution[0]` 是任意順序，**必須靠 `resourceDescription` 挑對期別**，否則會抓到 2018 年的檔案還以為是最新。
- `resourceAmount` 恆為 0。
- 年別欄位混用西元與民國且**標籤會說謊**：6281 欄名寫「（民國）」但值是西元 `19300101`；41685 欄名寫「113年1月至113年12月」但 `年度` 欄是 `2025`。
- 6281 最新一筆是 2023-09-14 公告、2024-01-01 實施的 27,470 元。`modifiedDate` 顯示 2026-06-18 但**內容並未更新到 2025/2026 年度基本工資**——modifiedDate 不等於資料涵蓋期。
- 44062 職缺清單恰好 1,000 列，是截斷上限而非實際職缺數。
- 所有 CSV 帶 UTF-8 BOM（`EF BB BF`）。
- `updateFrequency` 常為空物件內容（`frequency`/`unittime` 空字串），不可靠。

#### 能回答／不能回答

**能**：法定基本工資調整史；分行業×職類的年薪資與受僱人數（月經常性薪資 + 全年所得）；初任人員薪資分布；勞保／就保／勞退投保與提繳薪資（可當作有申報所得的分行業薪資 proxy，覆蓋率極高）；性別薪資差距；無薪假家數人數；就業服務機構名錄；當日職缺樣本的薪資帶與地點。

**不能**：任何工時／加班工時；月頻薪資（MOL 的薪資統計全部是年頻，只有失業認定、基金收益是月頻）；失業率與勞參率（那是主計總處人力資源調查）；企業層級薪資；縣市×行業交叉的薪資（只有全國分行業）；2024 年以後的基本工資（該資料集已 stale）。

---

### PCC 政府採購

#### A. 志工維運 API `pcc-api.openfun.app`（無 SLA，須標註來源）

`GET https://pcc-api.openfun.app/api/searchbytitle?query={關鍵字}&page={n}`

頂層 schema（實測）：
```json
{"query":"\"印刷\"","page":1,"total_records":10000,"total_pages":100,
 "took":0.224,"records":[…]}
```

`records[]` 每筆：

| 欄位 | 型別／格式 | 真實值 |
|---|---|---|
| `date` | int `yyyyMMdd` | `20260717` |
| `filename` | string | `ttd-71275355` |
| `brief.type` | string | `選擇性招標(建立合格廠商名單後續邀標)公告` / `決標公告` / `無法決標公告` |
| `brief.title` | string | `115年至117年經常性印刷品採購案第3次後續邀標(一般印刷及電腦套版印刷)` |
| `brief.category` | string（**部分筆缺此鍵**） | `勞務類884-附帶於製造業之服務…` |
| `brief.companies.ids` | string[] | `["97156416"]` |
| `brief.companies.names` | string[] | `["天地展覽室內裝修有限公司"]` |
| `brief.companies.id_key` | dict | `{"97156416":["投標廠商:投標廠商1:廠商代碼"]}` |
| `brief.companies.name_key` | dict | `{"天地展覽室內裝修有限公司":["投標廠商:投標廠商1:廠商名稱","決標品項:第1品項:得標廠商1:得標廠商"]}` |
| `job_number` | string | `1150122707`、`115-3000-1-031`、`NAMR115054` |
| `unit_id` | string（點分層級碼） | `3.79.3.1` |
| `unit_name` | string | `臺北市稅捐稽徵處` |
| `unit_api_url` / `tender_api_url` | string（**http，非 https**） | `http://pcc-api.openfun.app/api/tender?unit_id=…&job_number=…` |
| `unit_url` / `url` | 相對路徑 | `/index/case/3.79.3.1/1150122707/20260717/ttd-71275355` |

`GET /api/tender?unit_id=…&job_number=…` 回單案全歷程，`records[].detail` 是**中文冒號複合鍵**的扁平 dict：
```
"機關資料:機關代碼", "機關資料:機關名稱", "機關資料:單位名稱", "機關資料:機關地址",
"機關資料:聯絡人", "機關資料:聯絡電話", "機關資料:傳真號碼", "機關資料:電子郵件信箱",
"採購資料:標案案號", "採購資料:標案名稱", "採購資料:標的分類", "採購資料:財物採購性質",
"採購資料:採購金額級距", "採購資料:辦理方式", "採購資料:依據法條",
"採購資料:本採購是否屬「具敏感性或國安(含資安)疑慮之業務範疇」採購", …
```
另含 `detail.pkPmsMain`（Base64 主鍵，如 `NzEyNzE4NzQ`）與 `detail.url` → `https://web.pcc.gov.tw/tps/QueryTender/query/searchTenderDetail?pkPmsMain=…`

**`total_records: 10000` 已驗證為上限，非真實筆數。** 證據：
- `query=印刷` → `total_records:10000, total_pages:100`；`page=100` 正常回 100 筆；`page=101` 回 PHP warning + Elasticsearch 例外原文：
  `"Result window is too large, from + size must be less than or equal to: [10000] but was [10100]"`
- 對照組：`query=區塊鏈` → `total_records:180, total_pages:2`（真值）；`query=工程` → 10000（又撞頂）；不存在的詞 → `0`。
- 結論：`total_records < 10000` 時是真實命中數；**等於 10000 時只代表「≥10000」，且第 10001 筆之後無法透過此 API 取得**（要靠 unit/日期切分縮小結果集）。

**坑**
- 每頁固定 100 筆，硬上限 10,000 筆／查詢。
- 分頁越界不是 4xx，是 **HTTP 200 + PHP warning 混雜 JSON 的非法內容**，JSON parser 會爆。
- `unit_name` 有時等於 `unit_id`（實測 `"unit_name":"A.47.3"`），機關名稱缺失。
- `brief.category` 在部分公告型別（無法決標公告）不存在，取值要用 `.get()`。
- API URL 自我宣告為 `http://`，需自行改寫成 https。
- `query` 被自動加引號做片語比對（回應 `"query":"\"印刷\""`）。
- 志工專案、無 SLA、無版本承諾；引用時必須標註「資料來源：政府電子採購網，經 g0v/openfun pcc-api 重新整理」。

#### B. 官方 XML（耐用 fallback）

列表頁：`https://web.pcc.gov.tw/tps/tp/OpenData/showList`（另有 `showGPAList` 為 GPA 專用）

下載 URL 模式：
```
https://web.pcc.gov.tw/tps/tp/OpenData/downloadFile?fileName=tender_YYYYMM01.xml   ← 當月 1–15 日
https://web.pcc.gov.tw/tps/tp/OpenData/downloadFile?fileName=award_YYYYMM02.xml    ← 當月 16 日–月底
```
半月一檔。**tender（招標）與 award（決標）各 268 檔，涵蓋 `20150401` → `20260502`。** 頁面自述規則：「每個月 5 號會產出 2 個月前的資料，比如 10/5 會產出 8 月份的檔案」。2026-07-18 實測最新即 `20260502`（2026 年 5 月下半），**落後約 2.5 個月，與「約 2 個月」的記載相符**。授權：政府資料開放授權條款第 1 版。

`award_20260502.xml` schema（UTF-8、無 BOM、159,029 bytes、`<TENDER>` 共 156 筆）：
```xml
<?xml version="1.0" encoding="UTF-8"?>
<TENDER_LIST>
  <TENDER>
    <TENDER_AWARD_PRICE>230000000</TENDER_AWARD_PRICE>
    <PROCUREMENT_ATTR>工程類</PROCUREMENT_ATTR>
    <AWARD_DATE>2026/05/19</AWARD_DATE>
    <AWARD_NOTICE_DATE>2026/05/20</AWARD_NOTICE_DATE>
    <TENDER_TEL>(07)7995678分機2148</TENDER_TEL>
    <TENDER_ORG_NAME>高雄市政府水利局</TENDER_ORG_NAME>
    <TENDER_ORG_ADDR>830高雄市鳳山區光復路二段132號</TENDER_ORG_ADDR>
    <PROCUREMENT_TYPE>公開招標</PROCUREMENT_TYPE>
    <TENDER_NAME>典寶溪排水D區滯洪池工程(三 、四期)</TENDER_NAME>
    <CONTACT_PERSON>水利工程科-羅祥哲</CONTACT_PERSON>
    <TENDER_CASE_NO>B1150209</TENDER_CASE_NO>
    <TENDER_AWARD_WAY>最有利標</TENDER_AWARD_WAY>
    <BIDDER_LIST>
      <NOT_OBTAIN_SUPP_NAME>振勝營造有限公司</NOT_OBTAIN_SUPP_NAME>
      <BIDDER_SUPP_ADDR>820高雄市岡山區竹圍東街182巷10號1樓</BIDDER_SUPP_ADDR>
      <BIDDER_SUPP_NAME>超晟營造股份有限公司</BIDDER_SUPP_NAME>
    </BIDDER_LIST>
  </TENDER>
</TENDER_LIST>
```
| 欄位 | 單位／格式 |
|---|---|
| `TENDER_AWARD_PRICE` | 新台幣元，整數無分隔。實測 n=156，min 2,263,200／median 18,190,000／max 13,569,633,000 |
| `AWARD_DATE` / `AWARD_NOTICE_DATE` | **西元 `yyyy/MM/dd`**（注意與 openfun 的 `yyyyMMdd` int 不同） |
| `PROCUREMENT_ATTR` | 工程類／財物類／勞務類 |
| `PROCUREMENT_TYPE` | 公開招標／限制性招標(未經公開評選或公開徵求)／… |
| `TENDER_AWARD_WAY` | 最低標／最有利標 |
| `BIDDER_LIST` | **每個 TENDER 恰一組**（156 個 TENDER 對 156 個 BIDDER_LIST），多廠商案不會展開成多節點 |

`tender_20260502.xml`（126,148 bytes、326 筆）欄位較少：
```xml
<TENDER>
  <TENDER_SPDT>2026/06/22</TENDER_SPDT>
  <TENDER_ORG_NAME>中華郵政股份有限公司</TENDER_ORG_NAME>
  <TENDER_CASE_NO>115-7-35</TENDER_CASE_NO>
  <TENDER_NAME>郵政存簿儲金簿768萬本</TENDER_NAME>
  <PROCUREMENT_TYPE>公開招標</PROCUREMENT_TYPE>
  <PROCUREMENT_ATTR>財物類</PROCUREMENT_ATTR>
</TENDER>
```
`TENDER_SPDT` 是**開標日期**（可落在檔名期別之後，如 20260502 檔內出現 2026/06/22），不是公告日。

**坑**
- **這批 XML 是子集，不是全量**：半月僅 156 筆決標／326 筆招標，而同期 openfun 單一關鍵字就能回上千筆。頁面未載明篩選門檻；決標金額中位數 1,819 萬、最小 226 萬，看起來偏向大額案但無明確界線。**不可拿來算採購總額或家數市占**，只能當作大案的耐用查核來源。
- 不存在的期別（如 `award_20260601.xml`）回 **HTTP 200 + 0 bytes**，不是 404。抓取端必須檢查 `size_download > 0`。
- XML 內元素**順序不固定**（第 1 筆與第 2 筆 `<TENDER>` 的子元素排列不同），必須用 XML parser，不能用行序或 regex 位置。
- 無 `<RECORD>` 包裹層，根節點直接是 `<TENDER_LIST>`。
- `NOT_OBTAIN_SUPP_NAME`（未得標廠商）常為空元素 `<NOT_OBTAIN_SUPP_NAME></NOT_OBTAIN_SUPP_NAME>`。
- 決標檔**無統一編號**，只有廠商名稱字串；要做實體解析必須回頭用 openfun 的 `companies.ids` 或 GCIS 關鍵字查詢比對。

#### 能回答／不能回答

**能**：某廠商／某關鍵字的得標歷程與對手（openfun）；單案完整公告欄位；大額標案的機關、金額、決標方式時間序列（官方 XML）；透過 `companies.ids` 把採購紀錄接到統編。

**不能**：全國採購總額或分類別市場規模（openfun 撞 10,000 上限、官方 XML 是子集）；近 2 個月的官方權威資料（只能靠無 SLA 的 openfun）；廠商營收（決標金額 ≠ 營收，且只涵蓋公部門）；決標價的品項單價拆解（openfun detail 有部分品項欄，官方 XML 沒有）。

---

### GCIS 商工登記開放資料（`data.gcis.nat.gov.tw/od/data/api/{uuid}`）

免金鑰。回應 `Content-Type: application/json;charset=UTF-8`。

**權威 uuid 清單來源（本輪找到）**：`https://data.gcis.nat.gov.tw/resources/swagger/swagger.json`（49KB，Swagger 2.0，含 16 個 API 的 uuid、必填參數與 `$filter` 正則）。**不要用 `/od/datacategory` 頁面上的 uuid**——那是網站內部 `oid`，與 API uuid 完全不同，實測 8 個全部回 `此API不存在，請查明後繼續。`

| uuid | 名稱 | `$filter` 欄位 |
|---|---|---|
| `9D17AE0D-09B5-4732-A8F4-81ADED04B679` | 統編查公司名稱 | `Business_Accounting_NO eq` |
| `5F64D864-61CB-4D0D-8AD9-492047CC1EA6` | 公司登記基本資料-應用一 | `Business_Accounting_NO eq` |
| `F05D1060-7D57-4763-BDCE-0DAF5975AFE0` | 公司登記基本資料-應用二 | `Business_Accounting_NO eq` |
| `236EE382-4942-41A9-BD03-CA0709025E7C` | 公司登記基本資料-應用三（含營業項目） | `Business_Accounting_NO eq` |
| `4E5F7653-1B91-4DDC-99D5-468530FAE396` | 公司登記董監事資料集 | `Business_Accounting_NO eq` |
| `6BBA2268-1367-4B42-9CCA-BC17499EBE8C` | 公司登記關鍵字查詢 | **`Company_Name like … and Company_Status eq …`** |
| `4B61A0F1-458C-43F9-93F3-9FD6DA5E1B08` | 公司負責人資料查詢 | `Responsible_Name eq` |
| `F0E8FB8D-E2FD-472E-886C-91C673641F31` | 公司登記資本額查詢 | `Company_Status eq … and Capital_Stock_Amount eq [A-G]`（級距碼） |
| `FDB8D2C8-573D-4276-BFA4-8D3925ABE1CB` | 統編查分公司資料 | `Business_Accounting_NO eq` |
| `4347A009-6489-4F19-AC79-78F366BE7976` | 公司資料異動查詢 | `Change_Of_Approval_Data eq [0-9]{7}`（民國 7 碼） |
| `673F0FC0-B3A7-429F-9041-E9866836B66D` | 統編查是否為公司/分公司/商業 | `Business_Accounting_NO eq` |
| `FCB90AB1-E382-45CE-8D4F-394861851E28` | 公司行號營業項目代碼表 | — |
| `7E6AFA72-AD6A-46D3-8681-ED77951D912D` | 商業登記基本資料-應用一 | **`President_No eq` + `Agency eq`** |
| `F570BC9A-DA4C-4813-8087-FB9CE95F9D38` | 商業登記基本資料-應用二 | `President_No eq` |
| `426D5542-5F05-43EB-83F9-F1300F14E1F1` | 商業登記基本資料-應用三 | `President_No eq` |
| `C8782705-DA48-4897-8537-9F7B0FC463EF` | 營業項目代碼(F 零售、批發及餐飲業)查公司 | 營業項目碼 |

共同參數：`$format`（必填，json/xml）、`$filter`（必填）、`$skip`（0–500000）、`$top`（1–1000，預設 50）。

#### 真實回應

**應用一**（`5F64D864…`，`$filter=Business_Accounting_NO eq 22099131`）
```json
[{"Business_Accounting_NO":"22099131","Company_Status_Desc":"核准設立",
  "Company_Name":"台灣積體電路製造股份有限公司",
  "Capital_Stock_Amount":280500000000,"Paid_In_Capital_Amount":259323700670,
  "Share_Val":10,"Equity_Amt":25932370067,"Responsible_Name":"魏哲家",
  "Company_Location":"新竹科學園區新竹市力行六路8號",
  "Register_Organization_Desc":"國家科學及技術委員會新竹科學園區管理局",
  "Company_Setup_Date":"0760221","Change_Of_Approval_Data":"1150618",
  "Revoke_App_Date":"","Case_Status":"","Case_Status_Desc":"",
  "Sus_App_Date":"","Sus_Beg_Date":"","Sus_End_Date":""}]
```

**應用三**（含營業項目陣列）
```json
[{"Business_Accounting_NO":"22099131","Company_Name":"台灣積體電路製造股份有限公司",
  "Company_Status":"01","Company_Status_Desc":"核准設立","Company_Setup_Date":"0760221",
  "Cmp_Business":[{"Business_Seq_NO":"0001","Business_Item":"CC01080","Business_Item_Desc":"電子零組件製造業"},
                  {"Business_Seq_NO":"0002","Business_Item":"CC01090","Business_Item_Desc":"電池製造業"},
                  {"Business_Seq_NO":"0011","Business_Item":"       ","Business_Item_Desc":"１．依客戶之訂單與其提供之產品設計說明…"}]}]
```

**董監事**（`4E5F7653…`）
```json
[{"Person_Position_Name":"董事長","Person_Name":"魏哲家","Juristic_Person_Name":"","Person_Shareholding":7452349},
 {"Person_Position_Name":"董事","Person_Name":"葉俊顯","Juristic_Person_Name":"行政院國家發展基金管理會","Person_Shareholding":1653709980},
 {"Person_Position_Name":"獨立董事","Person_Name":"彼得‧邦菲爵士","Juristic_Person_Name":"","Person_Shareholding":0}]
```

**統編查分公司**（`FDB8D2C8…`，中華電信 96979933）
```json
[{"Business_Accounting_NO":"96979933","Branch_Office_Business_Accounting_NO":"27950876",
  "Branch_Office_Manager_Name":"張本元","Branch_Office_Status":"01","Branch_Office_Status_Desc":"核准設立",
  "Branch_Office_Name":"企業客戶分公司","Branch_Office_Location":"臺北市大安區信義路4段88號16樓",
  "BR_ESTAB_DATE":"0951229","CHG_APP_DATE":"1120724","Revoke_App_Date":"       ","_rowNum":1}]
```

**統編查類型**（`673F0FC0…`）
```json
[{"Year":"115","exist":"Y","TYPE":"公司"},{"Year":"115","exist":"N","TYPE":"分公司"},{"Year":"115","exist":"N","TYPE":"商業"}]
```

**負責人反查**（`4B61A0F1…`，`Responsible_Name eq 魏哲家`）
```json
[{"Business_Accounting_NO":"22099131","Company_Name":"台灣積體電路製造股份有限公司"}]
```

**關鍵字查詢**（`6BBA2268…`，`Company_Name like 台積電 and Company_Status eq 01`）
```json
[{"Business_Accounting_NO":"54900838","Company_Name":"台積電機有限公司","Company_Status":"01",
  "Company_Status_Desc":"核准設立","Capital_Stock_Amount":2000000,"Paid_In_Capital_Amount":0,
  "Responsible_Name":"王志聰","Register_Organization":"17","Register_Organization_Desc":"臺中市政府",
  "Company_Location":"臺中市南屯區春社里中台路61之3號",
  "Company_Setup_Date":"1040706","Change_Of_Approval_Data":"1091216"}]
```

#### 坑

- **「用公司名 `Company_Name like` 會回 400」這條記載不成立，要改寫。** 實際行為是：
  - 在 `9D17AE0D` / `5F64D864` 等統編型 API 上用 `Company_Name like` → **HTTP 200 + `Content-Length: 0` 空 body**（不是 400，也沒有錯誤訊息，會被誤判成「查無資料」）。
  - 想用公司名查，必須改用專屬的 **`6BBA2268-1367-4B42-9CCA-BC17499EBE8C` 公司登記關鍵字查詢**，且 `Company_Status` 為必要條件之一，該端點的 `like` 是**子字串比對**（查「台積電」會回「台積電機」「台積電梯」，不會回台積電本尊）。
- 完全沒有 `$filter` 時回 **HTTP 200 + 純文字 `$filter參數有誤，請查明後繼續。`**；uuid 錯誤回 **HTTP 200 + `此API不存在，請查明後繼續。`**。所有錯誤都是 200，**必須檢查 body 是否為合法 JSON**。
- 日期一律**民國 7 碼字串**、不足補零：`"0760221"` = 民國 76/02/21、`"1150618"` = 民國 115/06/18。與 fbfh 的西元 8 碼不同。
- 空值有三種寫法混用：`""`、`"       "`（7 個空白，如 `Revoke_App_Date`）、鍵不存在。
- `Business_Item` 可能是 7 個空白（自由填寫的營業項目文字寫在 `Business_Item_Desc`）。
- 金額欄是 JSON number（可超過 2^53？TSMC 資本額 280,500,000,000 仍安全，但解析時建議用 decimal）。`Paid_In_Capital_Amount` 在有限公司常為 `0`。
- 商業登記（獨資／合夥）用 `President_No` 不是 `Business_Accounting_NO`，且應用一還需 `Agency`（申登機關代碼）；只給 `President_No` 實測回空 body。
- `$top` 上限 1000、`$skip` 上限 500000，無法整批 dump 全部 162 萬家公司。

#### 能回答／不能回答

**能**：統編 → 公司名／狀態／資本額／實收資本／負責人／登記地址／設立日／最後核准變更日；統編 → 營業項目代碼清單（可當粗略行業分類）；統編 → 董監事名單與持股數；統編 → 所有分公司；負責人姓名 → 反查其名下公司；公司名關鍵字 → 統編（實體解析的主要入口）；`Change_Of_Approval_Data` 逐日掃描做增量更新。

**不能**：營收、獲利、員工數、進出口額——**登記資料完全沒有財務績效**（`Capital_Stock_Amount` 是登記資本額，不是營收，也不是市值）；未上市公司的股東名冊（只有董監事）；實質受益人；集團／母子公司關係（只有分公司，關係企業要靠董監事姓名與法人股東名稱自行 join）；歇業／停業的完整時間序列（只有 `Sus_*` 三個當期欄位）；產業統計（沒有「某行業共幾家」的彙總 API，只能靠營業項目查公司端點逐一分頁累加）。

---

### fbfh 出進口廠商登記名錄（`fbfh.trade.gov.tw/opendata/companyData.csv`）

**驗證方式**：`curl -r 0-120000`（Range 請求，伺服器支援，回 `HTTP/2 206`）。未下載全檔。

回應標頭（實測）：
```
HTTP/2 206
server: HiNetCDN
content-type: text/csv
content-range: bytes 0-120000/102944084
last-modified: Fri, 17 Jul 2026 00:01:00 GMT
etag: W/"102944084-1784246460953"
x-cache: MISS, EXPIRED, HIT
```

- **檔案大小 102,944,084 bytes（98.2 MiB）**
- **編碼 UTF-8 + BOM**（前 3 bytes `EF BB BF`）
- **日更**，`Last-Modified` 為當日 00:01 CST
- 全欄位加雙引號，逗號分隔，CRLF 未出現（單純 `\n`）
- **列數估算約 388,000 列**（樣本 450 列平均 265.2 bytes/列 → 102,944,084 ÷ 265.2 ≈ 388,214）。與「約 373k」的舊記載同量級，實際偏高約 4%。未下載全檔故為估計值。
- 依**統一編號升冪排序**：首列 `00000130`，末列 `99999912`。

#### Schema（12 欄，真實 header 逐字）

```
"統一編號","原始登記日期","核發日期","廠商中文名稱","廠商英文名稱","中文營業地址","英文營業地址","代表人","電話號碼","傳真號碼","進口資格","出口資格"
```

| 欄位 | 型別／格式 | 說明 |
|---|---|---|
| `統一編號` | 8 碼字串，**保留前導零** | `"00000130"`——必須以字串讀取，用 int 會掉 leading zero |
| `原始登記日期` | **西元 `yyyyMMdd`** | `"20241112"`（注意：GCIS 是民國 7 碼，兩者 join 時要轉） |
| `核發日期` | 西元 `yyyyMMdd` | `"20260423"`，可晚於原始登記日期（換證） |
| `廠商中文名稱` | string | `"健躍國際有限公司"` |
| `廠商英文名稱` | string | `"HEALTHUP TECHNOLOGY CO., LTD."`，大小寫不一致，含拼字錯誤（實測 `"wei sheng precision technoiogy CO., LTD."`） |
| `中文營業地址` | string | `"彰化縣溪湖鎮大突里地政路87號"` |
| `英文營業地址` | string | 含郵遞區號與 `Taiwan (R.O.C.)` 後綴 |
| `代表人` | **遮罩姓名** | `"賴O佳"`、`"曹O豪"`，可為空字串 |
| `電話號碼` | string | `"04-8681868#8603"`（含分機、格式不一），可空 |
| `傳真號碼` | string | 可空 |
| `進口資格` | **`有` / `無`** | 不是 Y/N、不是 1/0 |
| `出口資格` | **`有` / `無`** | |

#### 真實前 3 行

```
"00000130","20241112","20241112","健躍國際有限公司","HEALTHUP TECHNOLOGY CO., LTD.","彰化縣溪湖鎮大突里地政路87號","No. 87, Dizheng Rd., Datu Vil., Xihu Township, Changhua County 514020, Taiwan (R.O.C.)","賴O佳","04-8681868#8603","04-8681069","有","有"
"00000223","20250325","20250325","凱歐蘿數位多媒體有限公司","KOL Digital Multimedia CO., LTD.","臺北市信義區基隆路1段155號8樓之8","8 F.-8, No. 155, Sec. 1, Keelung Rd., Xinyi Dist., Taipei City 110058, Taiwan (R.O.C.)","曹O豪","","","有","有"
"00000429","20160620","20260423","盈鼎國際工商股份有限公司","FONG HUO WANG INTERNATIONAL CO., LTD.","臺北市信義區忠孝東路5段1號2樓","2 F., No. 1, Sec. 5, Zhongxiao E. Rd., Xinyi Dist., Taipei City 110410, Taiwan (R.O.C.)","","0933980112","","無","無"
```

末列（Range `102943000-102944083`）：
```
"99999912","20250306","20250306","品鑫和藏股份有限公司","Pinxin Harvest INC.","臺北市大安區延吉街251號5樓","5 F., No. 251, Yanji St., Da'an Dist., Taipei City 106068, Taiwan (R.O.C.)","李O弘","","","有","有"
```

#### 代表人遮罩格式（實測 450 列樣本）

- 格式：**保留姓 + 保留末字，中間全部換成單一個大寫拉丁字母 `O`**（U+004F，不是中文「〇」也不是 `●`）。
- 三字名 `賴O佳`、`曹O豪`、`沈O均`、`吳O心`、`曾O茹`、`江O澔`、`沈O年`、`吳O倫`、`黃O玲`、`陳O雲`、`古O綠`。
- 樣本 450 列中 **430 列含 `O`、20 列為空字串**（第 3 列 `盈鼎國際工商股份有限公司` 即為空）。
- 遮罩不可逆；要拿真實負責人須用 `統一編號` 去 GCIS `5F64D864…` 取 `Responsible_Name`（該欄未遮罩，實測 `"魏哲家"`）。

#### 樣本旗標分布（450 列，僅供感覺，非全檔）

`進口資格`：有 404／無 46；`出口資格`：有 402／無 48。

#### 坑

- 98 MB 日更全量檔，**沒有增量端點、沒有 API**。要做增量只能自行 diff 兩天的檔案（或用 `ETag`/`Last-Modified` 判斷是否重抓）。`ETag` 為 `W/"{size}-{epoch_ms}"`，size 變動即代表內容變動。
- 支援 Range 請求（206），可以只抓頭尾探測 schema 與排序範圍，不必落整份。
- UTF-8 BOM 會污染第一個欄名：pandas 要用 `encoding='utf-8-sig'`。
- `統一編號` 必須 `dtype=str`。
- `代表人`、`電話號碼`、`傳真號碼` 大量空字串，不是 NULL 標記。
- 中文地址無縣市／區的結構化欄位，要自己 parse；「臺」與「台」混用（實測地址用「臺北市」，但公司名用「台灣…」）。
- 英文名稱不可當唯一鍵（大小寫、標點、拼字皆不規範）。
- 沒有行業別、沒有產品別、沒有金額——見下。

#### 能回答／不能回答

**能**：全台約 38.8 萬家有出進口實績資格的廠商**名錄**；某統編是否具進口／出口資格；廠商登記地址（可做縣市／園區聚落分布計數）；登記與換證日期（可看新進廠商的時間分布）；作為**實體解析的橋樑**——用 `統一編號` 把 GCIS 登記資料、PCC 採購紀錄串起來，並判斷「這家公司有沒有在做進出口」。

**不能**：**這是名錄不是統計**。沒有按產品（HS code）或市場（國別）的家數統計；沒有進出口金額、數量、幣別；沒有實際交易紀錄或報關資料；沒有行業分類欄位（要 join GCIS 的 `Business_Item`）；沒有員工數或營收；代表人姓名已遮罩，無法直接做人物網絡分析；「有出口資格」不等於「今年有出口」——資格是登記狀態，不是實績。要金額層級的貿易數據須另找關務署／國貿署的貿易統計，本檔完全不含。

---

### 本輪未完成／失敗項目

| 目標 | 端點 | 失敗模式 |
|---|---|---|
| 月頻加班工時（主計總處） | `www.dgbas.gov.tw/public/data/open/EarningsProductivity/A046101010.csv` | HTTP 403（WAF） |
| 同上 | `winsta.dgbas.gov.tw/winsta/` | HTTP 404 |
| 同上 | `nstatdb.dgbas.gov.tw/dgbasall/webMain.aspx?...&outmode=8` | HTTP 200 但回 HTML 查詢介面，非 JSON/CSV；需帶 session 或改參數 |
| GCIS 資料集清單 | `data.gcis.nat.gov.tw/od/`、`/main/api` | HTTP 404（改用 `/od/datacategory` + `/resources/swagger/swagger.json` 成功） |

已依指示**未重試**：`wHandMenuFile.ashx`、`moeaic.gov.tw`、`data.gov.tw` 的 `/api/front/dataset/search` 與 `/api/v1/rest/dataset?q=`。附帶記錄：`data.gov.tw/api/v2/rest/dataset?q=…` 以 GET 呼叫回 **HTTP 405 `Method not allowed. Must be one of: POST`**——該路徑存在但僅接受 POST，可列為待驗證項而非死端點。