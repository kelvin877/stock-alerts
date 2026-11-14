# Stock Alerts

**English** · [中文](README.zh-HK.md)

A free, self-hosted stock watchlist with price alerts. It runs on GitHub (Actions + Pages) and sends push notifications to your phone via [ntfy](https://ntfy.sh). There's no server and no paid plan to keep running.

**Live page:** https://kelvin877.github.io/stock-alerts/

## Features

- **My Stocks**: a watchlist with live prices, company logos, daily change, day range, and this week's and this month's change. Pre-market and after-hours prices are labelled.
- **Price alerts**: on any stock, set "rises to ≥" or "falls to ≤" a target price. When it hits, you get a push notification. Each alert fires once; tap **Re-arm** to use it again.
- **Gainers / losers ranking** for your own watchlist: today, this week, or this month.
- **Movers**: the top 20 gainers and losers this week or this month, from about 540 US stocks (the S&P 500 plus popular names like SHOP, ASML, SOFI and RKLB).
- **Top 100**: the most traded stocks, ranked by average daily dollar volume over the last 20 trading days.
- Tap **＋** on any ranked stock to add it to your watchlist.
- **中文 / EN** switch in the top-right corner. Your choice is remembered on each device.
- Works on phone and desktop, with light and dark mode.

## How it works

| Part | What it does | How often |
|---|---|---|
| `index.html` | The web page, published with GitHub Pages | Whenever it changes |
| `.github/workflows/check.yml` → `scripts/check.py` | Fetches prices for your watchlist, checks alerts, and sends ntfy notifications | Every 5 min, Mon–Fri, 4:00–20:00 ET (pre-market to after-hours) |
| `.github/workflows/rankings.yml` → `scripts/rankings.py` | Builds the weekly and monthly movers and the Top 100 | Hourly during market hours, plus once after the close |

Data files in the repo:

- `alerts.json`: your watchlist and alerts. The web page writes this file.
- `prices.json`, `state.json`: latest prices and which alerts have fired. GitHub Actions writes these.
- `rankings.json`, `universe.json`: ranking results and the list of stocks they're picked from.

Prices come from Yahoo Finance and may be delayed by a few minutes.

## Setup (one time)

### 1. Get the ntfy app

Install **ntfy** from the App Store or Google Play. Tap **+**, subscribe to a topic, and pick a hard-to-guess name such as `stock-yourname-x7k2p9`. Anyone who knows the name can read your notifications, so don't use something simple.

### 2. Save the topic as a GitHub secret

Go to the repo's **Settings → Secrets and variables → Actions → New repository secret**:

- Name: `NTFY_TOPIC`
- Secret: the topic name from step 1

### 3. Turn on GitHub Pages

Go to **Settings → Pages**, set **Source** to **GitHub Actions**, then go to **Actions → 發佈網頁 (Publish page) → Run workflow**.

Your page will be at `https://<your-username>.github.io/stock-alerts/`.

### 4. Create a token for the web page

The page needs a token so it can save your watchlist.

1. Open https://github.com/settings/personal-access-tokens/new
2. **Token name**: anything, e.g. `stock-alerts-web`
3. **Expiration**: your choice. You'll need to regenerate the token when it expires.
4. **Repository access** → **Only select repositories** → choose this repo
5. **Permissions** → **Add permissions** → **Contents** → set to **Read and write**
6. Click **Generate token** and **copy it right away**. GitHub shows it only once.
7. On the web page, tap **⚙︎**, paste the token, and tap **Save**.

Do this on each device you use (phone, computer, and so on). The token is stored only in that browser.

### 5. Send a test notification

Go to **Actions → 檢查股價 (Check prices) → Run workflow**, tick **發一個測試通知 (send a test notification)**, and click **Run**. Your phone should get a "test notification" within a minute.

### Optional: English notifications

Notifications are in Chinese by default. To get them in English, go to **Settings → Secrets and variables → Actions → Variables → New repository variable**:

- Name: `NOTIFY_LANG`
- Value: `en`

## Using it

- **Add a stock**: type the ticker and tap **Add**. For US stocks, just use the ticker (`AAPL`). For Canadian stocks, add `.TO` for the TSX (`RY.TO`) or `.V` for the TSX Venture.
- **Set an alert**: tap **🔔 Set alert** on a stock, choose the condition and target price, then tap **Save alert**. If the price is already past the target, the page warns you that the alert will fire on the next check.
- **Rank your watchlist**: tap **▲ Top gainers** or **▼ Top losers**, then choose **Today / This week / This month**. Tap **List** to go back.
- **Remove a stock**: tap **Remove**. This also deletes that stock's alerts.

## FAQ

**What happens when the token expires?**
Alerts and rankings keep working, because GitHub Actions doesn't use your token. You just can't edit the watchlist from the page until you regenerate the token at https://github.com/settings/personal-access-tokens (open the token → **Regenerate token**) and paste the new one in **⚙︎**.

**Can other people change my watchlist?**
No. The repo is public, so anyone can *see* your watchlist, but only you (or collaborators you add) can change it. Keep your token private. If you think it has leaked, delete it on the tokens page and create a new one.

**I deleted something by mistake.**
Every change is saved in git history. Open `alerts.json` → **History** in the repo, find the old version, and restore it.

**Can someone else use this with their own list?**
Yes. They fork this repo into their own GitHub account and follow the setup steps above with their own ntfy topic and token.

**Why didn't an alert fire right on time?**
GitHub's scheduled runs can be delayed by several minutes when GitHub is busy, and rankings may update less often than hourly. This isn't suitable for second-by-second trading.

## Limits

- Rankings cover US stocks only. Canadian stocks work in your watchlist and alerts, but they aren't in the Movers or Top 100 lists.
- Free GitHub Actions minutes are unlimited for public repos. If you make this repo private, the 5-minute schedule will use up the free minutes quickly.
- Some company logos may not load and will show as a blank or a coloured letter.
