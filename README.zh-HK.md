# 股價通知

[English](README.md) · **中文**

一個免費、自己架設嘅股票觀察清單同到價通知系統。靠 GitHub（Actions + Pages）運作，經 [ntfy](https://ntfy.sh) 推送通知去你部電話，唔使伺服器，亦唔使俾錢。

**網頁：** https://kelvin877.github.io/stock-alerts/

## 功能

- **我的股票**：觀察清單，顯示即時股價、公司 logo、今日升跌、今日高低位、本週同本月升跌，盤前／盤後價會標明。
- **到價通知**：每隻股票都可以設「升到 ≥」或者「跌到 ≤」目標價，到價就推送通知。每個通知響一次，撳「重新開」可以再用。
- **觀察清單升跌排名**：今日／本週／本月。
- **升跌排行**：本週或本月全市場升跌 Top 20，由大約 540 隻美股入面揀（S&P 500 加 SHOP、ASML、SOFI、RKLB 等熱門股）。
- **熱門 100**：按過去 20 個交易日平均每日成交額排名。
- 排行榜每隻股票旁邊撳 **＋** 就可以加入觀察清單。
- 右上角有 **中文 / EN** 掣，每部機會記住你揀咗邊個語言。
- 電話同電腦都用得，支援深色模式。

## 點樣運作

| 部分 | 做咩 | 幾耐一次 |
|---|---|---|
| `index.html` | 網頁，用 GitHub Pages 發佈 | 有改動先會更新 |
| `.github/workflows/check.yml` → `scripts/check.py` | 攞觀察清單股價、檢查通知、發 ntfy 推送 | 星期一至五美東 4:00–20:00（盤前至盤後），每 5 分鐘 |
| `.github/workflows/rankings.yml` → `scripts/rankings.py` | 計本週、本月升跌排行同熱門 100 | 開市時間每個鐘，收市後再一次 |

Repo 入面嘅數據檔：

- `alerts.json`：觀察清單同通知設定，由網頁寫入。
- `prices.json`、`state.json`：最新股價同邊啲通知已經觸發，由 GitHub Actions 寫入。
- `rankings.json`、`universe.json`：排行結果同排行用嘅股票名單。

股價來自 Yahoo Finance，可能有幾分鐘延遲。

## 設定步驟（一次過）

1. **ntfy**：喺電話裝 ntfy app，撳 **+** 訂閱一個難估嘅 topic 名，例如 `stock-yourname-x7k2p9`。任何人知道個名都收到你嘅通知，所以唔好改得太簡單。
2. **Secret**：repo → **Settings → Secrets and variables → Actions → New repository secret**
   - Name：`NTFY_TOPIC`
   - Secret：第 1 步嘅 topic 名
3. **GitHub Pages**：**Settings → Pages**，Source 揀 **GitHub Actions**。然後去 **Actions → 發佈網頁 → Run workflow**。
4. **Token**（網頁儲存設定用）：
   1. 打開 https://github.com/settings/personal-access-tokens/new
   2. 名隨便改，例如 `stock-alerts-web`。有效期自己揀，過期就要整過。
   3. **Repository access** → **Only select repositories** → 揀呢個 repo
   4. **Permissions** → **Add permissions** → **Contents** → **Read and write**
   5. 撳 **Generate token**，然後**即刻複製**，因為只會顯示一次。
   6. 喺網頁撳 **⚙︎**，貼入 token，再撳儲存。每部機都要各自貼一次。
5. **測試**：**Actions → 檢查股價 → Run workflow**，剔「發一個測試通知」再撳 Run，你部電話應該會收到測試通知。

**想收英文通知（可選）：** 去 **Settings → Secrets and variables → Actions → Variables → New repository variable**，Name 填 `NOTIFY_LANG`，Value 填 `en`。

## 用法

- **加股票**：輸入代號撳「加入」。美股直接打代號（`AAPL`）；加股多倫多加 `.TO`（`RY.TO`），創業板加 `.V`。
- **設通知**：撳股票嘅「🔔 設通知」，揀條件同目標價，再撳「儲存通知」。如果而家個價已經過咗目標，網頁會提你下次 check 就會即刻觸發。
- **觀察清單排名**：撳「▲ 升幅排名」或者「▼ 跌幅排名」，再揀今日／本週／本月。撳「清單」就返去原本嘅卡片。
- **移除股票**：撳「移除」，嗰隻股票嘅通知都會一齊刪除。

## 常見問題

**Token 過期會點？**
通知同排行照常運作，因為 GitHub Actions 唔使用你個 token。不過要喺 https://github.com/settings/personal-access-tokens 撳你個 token → **Regenerate token**，再喺網頁 ⚙︎ 貼新嘅 token，先可以再喺網頁改清單。

**其他人可唔可以改我嘅清單？**
唔可以。Repo 係 public，所以其他人**睇**得到，但只有你同你加嘅 collaborator 先**改**得到。Token 唔好俾人；懷疑外洩就刪咗佢，再整過一個。

**唔小心刪咗嘢點算？**
每次改動都有紀錄。喺 repo 打開 `alerts.json` → **History**，搵返舊版本還原就得。

**其他人想用自己一份清單？**
用佢自己嘅 GitHub 帳戶 fork 呢個 repo，再跟上面步驟設定自己嘅 ntfy topic 同 token。

**點解通知唔係準時響？**
GitHub 繁忙時，定時任務可能遲幾分鐘；排行亦可能少過每個鐘更新一次。唔適合要秒級反應嘅交易。

## 限制

- 排行只包括美股。加股可以放入觀察清單同設通知，但唔會出現喺排行同熱門 100。
- Public repo 用 GitHub Actions 冇時間上限。如果改做 private，每 5 分鐘一次嘅排程好快會用晒免費額度。
- 有啲公司 logo 可能顯示唔到，會變成空白或者一個有顏色嘅字母。
