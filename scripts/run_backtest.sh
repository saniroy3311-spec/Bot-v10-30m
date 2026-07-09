#!/bin/bash
set -e

echo "=== 1. Downloading 1-Year Binance BTC/USDT 30m OHLCV Candles ==="
python3 scripts/download_candles.py

echo "=== 2. Running Backtest Engine (1-Year Period) ==="
python3 backtest.py --csv btc_30m_1y.csv --out bt_trades.csv --signals bt_signals.jsonl

echo "=== 3. Compiling Metrics & Generating HTML Report Dashboard ==="
python3 scripts/generate_backtest_report.py

echo "=========================================================="
echo "Backtest Report Generated Successfully!"
echo "You can view the dashboard live at:"
echo "http://187.127.136.139:9030/backtest"
echo "=========================================================="
