#!/usr/bin/env python3
"""Check stock prices against alerts.json and send ntfy notifications.

Reads:  alerts.json  (written by the web page)
Writes: prices.json  (latest prices, shown on the web page)
        state.json   (which alerts have already fired)

Env:
  NTFY_TOPIC   ntfy topic to publish to (required to notify)
  NTFY_SERVER  defaults to https://ntfy.sh
  FORCE=1      run even outside US/Canada extended trading hours
  TEST_NOTIFY=1 send a test notification
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ET = ZoneInfo("America/New_York")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")


def load(name, default):
    try:
        with open(os.path.join(ROOT, name), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def save(name, data):
    with open(os.path.join(ROOT, name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.write("\n")


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def market_open(now=None):
    """True during US extended hours (4:00-20:00 ET, Mon-Fri). TSX hours fall inside."""
    now = (now or datetime.now(timezone.utc)).astimezone(ET)
    if now.weekday() >= 5:
        return False
    minutes = now.hour * 60 + now.minute
    return 4 * 60 <= minutes < 20 * 60


def fetch_quote(symbol):
    path = ("/v8/finance/chart/" + urllib.parse.quote(symbol)
            + "?interval=1m&range=1d&includePrePost=true")
    data, last_err = None, None
    for host in ("query1.finance.yahoo.com", "query2.finance.yahoo.com"):
        try:
            req = urllib.request.Request("https://" + host + path, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.load(r)
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise ValueError("搵唔到呢個股票代號") from e
            last_err = e
        except Exception as e:
            last_err = e
    if data is None:
        raise last_err
    result = (data.get("chart") or {}).get("result")
    if not result:
        err = ((data.get("chart") or {}).get("error") or {}).get("description")
        raise ValueError(err or "搵唔到呢個股票代號")
    return parse_chart(result[0])


def parse_chart(res):
    meta = res.get("meta") or {}
    stamps = res.get("timestamp") or []
    quote = ((res.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    price, ts = None, None
    # Latest non-empty 1-minute bar, including pre/after-hours.
    for t, c in zip(reversed(stamps), reversed(closes[:len(stamps)])):
        if c is not None:
            price, ts = c, t
            break
    if price is None:
        price, ts = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
    if price is None:
        raise ValueError("攞唔到價")
    return {
        "price": round(float(price), 4),
        "currency": meta.get("currency"),
        "name": meta.get("shortName") or meta.get("longName") or meta.get("symbol"),
        "prev_close": meta.get("chartPreviousClose") or meta.get("previousClose"),
        "time": ts,
    }


def hit(alert, price):
    target = float(alert["price"])
    return price >= target if alert.get("condition") == "above" else price <= target


def notify(topic, title, message, tags, priority=4):
    server = os.environ.get("NTFY_SERVER", "https://ntfy.sh").rstrip("/")
    body = json.dumps({
        "topic": topic, "title": title, "message": message,
        "tags": tags, "priority": priority,
    }).encode("utf-8")
    req = urllib.request.Request(server, data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def fmt(v):
    return f"{v:,.4f}".rstrip("0").rstrip(".") if v < 1 else f"{v:,.2f}"


def main(fetch=fetch_quote, send=notify):
    topic = os.environ.get("NTFY_TOPIC", "").strip()
    force = os.environ.get("FORCE") == "1"

    if os.environ.get("TEST_NOTIFY") == "1":
        if not topic:
            print("::error::未設定 NTFY_TOPIC secret")
            return 1
        send(topic, "測試通知 ✅", "股價通知設定成功！到價嗰陣你會收到呢類通知。", ["white_check_mark"], 3)
        print("Sent test notification")

    if not force and not market_open():
        print("Outside trading hours, skipping.")
        return 0

    alerts = [a for a in load("alerts.json", {"alerts": []}).get("alerts", [])
              if a.get("id") and a.get("symbol")]
    state = load("state.json", {})
    old_prices = load("prices.json", {}).get("prices", {})

    symbols = sorted({a["symbol"].upper() for a in alerts})
    prices = {}
    for sym in symbols:
        try:
            prices[sym] = fetch(sym)
        except Exception as e:  # keep going with other symbols
            print(f"{sym}: {e}")
            prev = old_prices.get(sym) or {}
            prices[sym] = {**{k: v for k, v in prev.items() if k != "error"}, "error": str(e)[:200]}

    for a in alerts:
        if a["id"] in state or a.get("active") is False:
            continue
        q = prices.get(a["symbol"].upper()) or {}
        if "price" not in q or q.get("error"):
            continue
        p = q["price"]
        if not hit(a, p):
            continue
        if not topic:
            print("::warning::到價但未設定 NTFY_TOPIC，冇發通知")
            continue
        up = a.get("condition") == "above"
        title = f"{a['symbol'].upper()} {'升到' if up else '跌到'} {fmt(p)}"
        msg = f"目標：{'≥' if up else '≤'} {fmt(float(a['price']))} {q.get('currency') or ''}".strip()
        if q.get("name"):
            msg = f"{q['name']}\n{msg}"
        if a.get("note"):
            msg += f"\n備註：{a['note']}"
        try:
            send(topic, title, msg, ["chart_with_upwards_trend" if up else "chart_with_downwards_trend"])
        except Exception as e:
            print(f"::warning::通知發送失敗，下次再試：{e}")
            continue
        state[a["id"]] = {"triggered_at": now_iso(), "price": p}
        print(f"Triggered {a['id']} {title}")

    ids = {a["id"] for a in alerts}
    state = {k: v for k, v in state.items() if k in ids}
    save("state.json", state)
    save("prices.json", {"updated": now_iso(), "prices": prices})
    return 0


if __name__ == "__main__":
    sys.exit(main())
