# 股價通知

一個網頁畀你加股票同設目標價，GitHub Actions 喺美股盤前至盤後（美東 4am–8pm，即溫哥華 1am–5pm，星期一至五）每 5 分鐘 check 一次價，到價就經 ntfy 推送通知去你部電話。

## 設定步驟（一次過）

1. **ntfy**：喺電話裝 ntfy app → 撳「+」訂閱一個 topic，改個難估嘅名，例如 `stock-k8f2q9x`（任何人知道個名都可以收你嘅通知，所以唔好改得太簡單）。
2. **Secret**：repo → Settings → Secrets and variables → Actions → New repository secret
   - Name：`NTFY_TOPIC`
   - Secret：你喺第 1 步用嘅 topic 名
3. **GitHub Pages**：repo → Settings → Pages → Source 揀 **GitHub Actions**。然後去 Actions → 「發佈網頁」→ Run workflow。網址會係 `https://你個用戶名.github.io/repo名/`。
4. **Token**（網頁要用嚟儲存通知）：GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens → Generate new token
   - Repository access：Only select repositories → 揀呢個 repo
   - Permissions → Repository permissions → **Contents：Read and write**
   - 複製個 token，喺網頁右上「設定」貼入去
5. **測試**：Actions → 「檢查股價」→ Run workflow → 剔「發一個測試通知」→ Run。你部電話應該會收到「測試通知 ✅」。

## 用法

- 美股直接打代號（AAPL）；加股要加 `.TO`（RY.TO）或者 `.V`。
- 每個通知觸發一次之後就會停，撳「重新開」可以再開。
- 加完新通知大約一分鐘內會攞到價。

## 注意

- 呢個 repo 係 public，所以你設咗咩股票同價位，其他人都睇得到（ntfy topic 收埋喺 secret，唔會公開）。
- 價格嚟自 Yahoo Finance，可能有少少延遲；GitHub 嘅定時任務繁忙時間都可能遲幾分鐘，唔適合要秒級反應嘅交易。
