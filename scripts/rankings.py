#!/usr/bin/env python3
"""Build rankings.json: this month's top 20 gainers / losers and the 100 most
traded (by average daily dollar volume) stocks, from the list in universe.json.

Run by .github/workflows/rankings.yml.
"""
import csv
import io
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check import ET, UA, load, now_iso, save  # noqa: E402

SP500_CSV = ("https://raw.githubusercontent.com/datasets/"
             "s-and-p-500-companies/main/data/constituents.csv")


def refresh_universe():
    """Update the S&P 500 part of universe.json; keep the old list on failure."""
    uni = load("universe.json", {"symbols": {}})
    symbols = dict(uni.get("symbols", {}))
    try:
        req = urllib.request.Request(SP500_CSV, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=20) as r:
            rows = list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))
        if len(rows) > 400:
            for row in rows:
                symbols.setdefault(row["Symbol"].replace(".", "-"), row["Security"])
    except Exception as e:
        print(f"Universe refresh failed, using saved list: {e}")
    return symbols


def fetch_daily(symbol):
    path = ("/v8/finance/chart/" + urllib.parse.quote(symbol)
            + "?interval=1d&range=3mo")
    last = None
    for attempt in range(3):
        host = ("query1", "query2")[attempt % 2] + ".finance.yahoo.com"
        try:
            req = urllib.request.Request("https://" + host + path, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            res = (data.get("chart") or {}).get("result")
            if not res:
                return None
            return res[0]
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            last = e
            time.sleep(1.5 * (attempt + 1))
        except Exception as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    print(f"{symbol}: {last}")
    return None


def summarize(symbol, name, res, month_start_ts):
    meta = res.get("meta") or {}
    stamps = res.get("timestamp") or []
    q = ((res.get("indicators") or {}).get("quote") or [{}])[0]
    closes, vols = q.get("close") or [], q.get("volume") or []
    bars = [(t, c, v or 0) for t, c, v in zip(stamps, closes, vols) if c is not None]
    if len(bars) < 2:
        return None
    price = meta.get("regularMarketPrice") or bars[-1][1]
    before = [b for b in bars if b[0] < month_start_ts]
    base = before[-1][1] if before else bars[0][1]
    # Previous session close: the bar before today's, if today's bar exists.
    def day(ts):
        return datetime.fromtimestamp(ts, ET).date()
    rmt = meta.get("regularMarketTime")
    today_bar = rmt is not None and day(bars[-1][0]) == day(rmt)
    prev_close = bars[-2][1] if today_bar else bars[-1][1]
    recent = bars[-20:]
    dollar_vol = sum(c * v for _, c, v in recent) / len(recent)
    return {
        "symbol": symbol,
        "name": meta.get("shortName") or meta.get("longName") or name,
        "price": round(float(price), 4),
        "currency": meta.get("currency"),
        "month_base": round(float(base), 4),
        "month_pct": round((price - base) / base * 100, 2) if base else None,
        "day_pct": round((price - prev_close) / prev_close * 100, 2) if prev_close else None,
        "dollar_volume": round(dollar_vol),
        "avg_volume": round(sum(v for _, _, v in recent) / len(recent)),
    }


def main():
    symbols = refresh_universe()
    now_et = datetime.now(timezone.utc).astimezone(ET)
    month_start = now_et.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_ts = int(month_start.timestamp())

    def work(item):
        sym, name = item
        res = fetch_daily(sym)
        return summarize(sym, name, res, month_start_ts) if res else None

    with ThreadPoolExecutor(max_workers=6) as pool:
        rows = [r for r in pool.map(work, sorted(symbols.items())) if r]

    print(f"Fetched {len(rows)} / {len(symbols)} symbols")
    if len(rows) < len(symbols) * 0.5:
        print("::error::Too many symbols failed; keeping previous rankings.json")
        return 1

    movers = [r for r in rows if r["month_pct"] is not None]
    movers.sort(key=lambda r: r["month_pct"], reverse=True)
    popular = sorted(rows, key=lambda r: r["dollar_volume"], reverse=True)

    save("rankings.json", {
        "updated": now_iso(),
        "month": month_start.strftime("%Y-%m"),
        "universe_size": len(rows),
        "gainers": movers[:20],
        "losers": movers[::-1][:20],
        "popular": popular[:100],
    })
    save("universe.json", {
        "source": "S&P 500 (datasets/s-and-p-500-companies) + popular extras",
        "symbols": symbols,
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
