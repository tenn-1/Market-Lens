"""
Market Lens API — live stock data backend using yfinance.

Endpoints:
  GET /api/search?q=apple          -> [{symbol, name, exchange}, ...]
  GET /api/stock/<ticker>?range=6M -> OHLCV + MA20/MA200/RSI/MACD/Bollinger
                                       + golden/death cross dates

range values: 1M, 6M, 1Y, 2Y, 3Y

Data is cached in memory for CACHE_TTL seconds per (ticker, range) so the
dashboard always gets fresh-enough prices without hammering Yahoo on every
click.
"""
import time
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)  # allow the dashboard (any origin, e.g. GitHub Pages) to call this API

CACHE_TTL = 60 * 5  # 5 minutes
_cache = {}

RANGE_MAP = {'1M': '1mo', '6M': '6mo', '1Y': '1y', '2Y': '2y', '3Y': '3y'}


def rsi(series, window=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(50)


def macd(series, fast=12, slow=26, signal=9):
    ema_f = series.ewm(span=fast, adjust=False).mean()
    ema_s = series.ewm(span=slow, adjust=False).mean()
    line = ema_f - ema_s
    sig = line.ewm(span=signal, adjust=False).mean()
    return line, sig


def clean(series):
    """Convert a pandas Series to a plain list with real Python None in place
    of NaN. pandas' .where(cond, None) does NOT work for this on float
    columns -- it silently coerces None back to NaN, which then serializes
    as the invalid JSON token `NaN` and breaks the browser's JSON.parse()."""
    return [None if pd.isna(v) else float(v) for v in series]


def find_crosses(ma20, ma200):
    diff = (ma20 - ma200).dropna()
    sign = np.sign(diff)
    flips = sign.diff().fillna(0)
    golden = diff.index[flips == 2].tolist()
    death = diff.index[flips == -2].tolist()
    return golden, death


@app.route('/api/search')
def search():
    q = request.args.get('q', '').strip()
    if len(q) < 1:
        return jsonify([])
    key = f'search:{q.lower()}'
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return jsonify(hit[1])
    try:
        # Yahoo Finance's public (unofficial) search endpoint — returns any ticker, not a fixed list
        r = requests.get(
            'https://query1.finance.yahoo.com/v1/finance/search',
            params={'q': q, 'quotesCount': 8, 'newsCount': 0},
            headers={'User-Agent': 'Mozilla/5.0'}, timeout=5
        )
        quotes = r.json().get('quotes', [])
        results = [{
            'symbol': x.get('symbol'),
            'name': x.get('shortname') or x.get('longname') or x.get('symbol'),
            'exchange': x.get('exchange', '')
        } for x in quotes if x.get('symbol') and x.get('quoteType') == 'EQUITY']
        _cache[key] = (time.time(), results)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 502


@app.route('/api/stock/<ticker>')
def stock(ticker):
    ticker = ticker.upper()
    rng = request.args.get('range', '1Y')
    period = RANGE_MAP.get(rng, '1y')
    key = f'stock:{ticker}:{period}'
    hit = _cache.get(key)
    if hit and time.time() - hit[0] < CACHE_TTL:
        return jsonify(hit[1])

    try:
        tk = yf.Ticker(ticker)
        df = tk.history(period='3y', auto_adjust=True)  # fetch 3y once, slice per range
        if df.empty:
            return jsonify({'error': f'No data for {ticker}'}), 404

        close = df['Close']
        ma20, ma200 = close.rolling(20).mean(), close.rolling(200).mean()
        rsi14 = rsi(close)
        macd_line, macd_sig = macd(close)
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        golden, death = find_crosses(ma20, ma200)

        info = {}
        try:
            info = tk.info or {}
        except Exception:
            pass

        payload = {
            'ticker': ticker,
            'name': info.get('shortName') or info.get('longName') or ticker,
            'sector': info.get('sector', 'N/A'),
            'dates': df.index.strftime('%Y-%m-%d').tolist(),
            'close': close.round(2).tolist(),
            'volume': df['Volume'].astype(int).tolist(),
            'ma20': clean(ma20.round(2)),
            'ma200': clean(ma200.round(2)),
            'rsi14': clean(rsi14.round(1)),
            'macd': clean(macd_line.round(3)),
            'macdSignal': clean(macd_sig.round(3)),
            'bbUpper': clean((bb_mid + 2 * bb_std).round(2)),
            'bbLower': clean((bb_mid - 2 * bb_std).round(2)),
            'goldenCrosses': [d.strftime('%Y-%m-%d') for d in golden],
            'deathCrosses': [d.strftime('%Y-%m-%d') for d in death],
            'fetchedAt': int(time.time()),
        }
        _cache[key] = (time.time(), payload)
        return jsonify(payload)
    except Exception as e:
        return jsonify({'error': str(e)}), 502


@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'cached_items': len(_cache)})


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)