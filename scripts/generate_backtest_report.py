import pandas as pd
import json
import os
import datetime

def generate_report():
    csv_path = "bt_trades.csv"
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found! Run the backtest first.")
        return
        
    df = pd.read_csv(csv_path)
    if df.empty:
        print("No trades in bt_trades.csv!")
        return

    # overall metrics
    total_trades = len(df)
    wins = df[df["real_pl"] > 0]
    losses = df[df["real_pl"] <= 0]
    win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0
    
    total_profit = df["real_pl"].sum()
    max_profit = df["real_pl"].max()
    max_loss = df["real_pl"].min()
    
    avg_win = wins["real_pl"].mean() if not wins.empty else 0.0
    avg_loss = losses["real_pl"].mean() if not losses.empty else 0.0
    
    profit_factor = (wins["real_pl"].sum() / abs(losses["real_pl"].sum())) if not losses.empty and losses["real_pl"].sum() != 0 else 1.0

    # Calculate Max Drawdown
    starting_cap = 10000.0
    equity = starting_cap
    equity_series = [starting_cap]
    for pl in df["real_pl"]:
        equity += pl
        equity_series.append(equity)
        
    peaks = pd.Series(equity_series).cummax()
    drawdowns = (peaks - pd.Series(equity_series)) / peaks * 100
    max_dd = drawdowns.max()

    # Calculate monthly P/L
    df["exit_date"] = pd.to_datetime(df["exit_ts"], unit="ms")
    df["month"] = df["exit_date"].dt.strftime("%Y-%m")
    monthly_pl = df.groupby("month")["real_pl"].sum().reset_index()
    monthly_pl_list = monthly_pl.to_dict(orient="records")

    # Serialize trades for Javascript
    trades_json = []
    equity = starting_cap
    for i, row in df.iterrows():
        equity += row["real_pl"]
        entry_time = pd.to_datetime(row["entry_ts"], unit="ms").strftime("%Y-%m-%d %H:%M:%S")
        exit_time = pd.to_datetime(row["exit_ts"], unit="ms").strftime("%Y-%m-%d %H:%M:%S")
        
        trades_json.append({
            "id": int(row["trade_id"]),
            "signal_type": str(row["signal_type"]),
            "is_long": bool(row["is_long"]),
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_price": float(row["entry_price"]),
            "exit_price": float(row["exit_price"]),
            "points_captured": float(row["points_captured"]) if "points_captured" in df.columns else float(row["exit_price"] - row["entry_price"] if row["is_long"] else row["entry_price"] - row["exit_price"]),
            "real_pl": float(row["real_pl"]),
            "exit_reason": str(row["exit_reason"]),
            "equity": float(equity)
        })

    # Prepare template HTML
    html_template = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Backtest Report - Shiva Sniper Gold Bot</title>
<style>
  :root {
    --bg: #0b0e14;
    --panel: #12161f;
    --line: #232838;
    --text: #e8eaf0;
    --dim: #7c8496;
    --green: #3ecf8e;
    --red: #ef5b5b;
    --amber: #e8a33d;
    --mono: 'SF Mono', 'JetBrains Mono', Consolas, monospace;
  }
  body.light {
    --bg: #f9fafb;
    --panel: #ffffff;
    --line: #e5e7eb;
    --text: #111827;
    --dim: #4b5563;
  }
  body.light thead th {
    background: #f3f4f6;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0; padding: 12px; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    transition: background 0.15s, color 0.15s;
  }
  .wrap { max-width: 1400px; margin: 0 auto; padding: 12px; }
  .topbar {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--panel); border: 1px solid var(--line); border-radius: 8px;
    padding: 14px 18px; margin-bottom: 14px; flex-wrap: wrap; gap: 12px;
  }
  .topbar .title { font-size: 15px; font-weight: 700; letter-spacing: .3px; }
  .topbar .title .dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:var(--green); margin-right:8px; box-shadow:0 0 6px var(--green); }
  .topbar .sub { color: var(--dim); font-size: 11px; margin-top: 2px; font-family: var(--mono); }

  .grid6 { display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 14px; }
  @media (max-width: 1100px) { .grid6 { grid-template-columns: repeat(3, 1fr); } }
  @media (max-width: 600px) {
    .grid6 { grid-template-columns: 1fr; }
    .topbar { flex-direction: column; align-items: flex-start; gap: 10px; }
    .topbar > div { width: 100%; display: flex; justify-content: space-between; align-items: center; }
  }

  .card {
    background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px;
  }
  .card h3 {
    margin: 0 0 10px 0; font-size: 10px; letter-spacing: .8px; color: var(--dim);
    text-transform: uppercase; font-weight: 700; border-bottom: 1px solid var(--line); padding-bottom: 8px;
  }
  .card .v { font-family: var(--mono); font-size: 18px; font-weight: 700; }
  .card .v.pos { color: var(--green); }
  .card .v.neg { color: var(--red); }

  .eq-card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px; margin-bottom: 14px; position: relative; }
  .eq-card h3 { margin: 0 0 12px 0; font-size: 10.5px; letter-spacing: .8px; color: var(--dim); text-transform: uppercase; font-weight: 700; }

  .split-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
  @media (max-width: 768px) { .split-grid { grid-template-columns: 1fr; } }

  .table-card { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 0; overflow: hidden; }
  .table-head { padding: 14px 16px 10px; display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid var(--line); }
  .table-head h3 { margin:0; font-size: 10.5px; letter-spacing:.8px; color: var(--dim); text-transform: uppercase; font-weight:700; }
  
  .table-scroll { max-height: 400px; overflow-y: auto; -webkit-overflow-scrolling: touch; }
  table { width: 100%; border-collapse: collapse; font-family: var(--mono); font-size: 11.5px; }
  thead th {
    position: sticky; top: 0; background: #171c28; color: var(--dim);
    text-align: left; padding: 8px 14px; font-size: 10px; letter-spacing: .5px;
    text-transform: uppercase; border-bottom: 1px solid var(--line); z-index: 1;
  }
  tbody td { padding: 7px 14px; border-bottom: 1px solid var(--line); }
  tbody tr:hover { background: rgba(255,255,255,.02); }
  td.num { text-align: right; }
  .pos { color: var(--green); }
  .neg { color: var(--red); }
  .badge { font-family: var(--mono); font-size: 10px; font-weight: 700; padding: 2px 8px; border-radius: 4px; }
  .badge.long { background: rgba(62,207,142,.12); color: var(--green); border: 1px solid rgba(62,207,142,.35); }
  .badge.short { background: rgba(239,91,91,.12); color: var(--red); border: 1px solid rgba(239,91,91,.35); }

  ::-webkit-scrollbar { width: 8px; height: 8px; }
  ::-webkit-scrollbar-thumb { background: var(--line); border-radius: 4px; }
</style>
</head>
<body>
<div class="wrap">
  <div class="topbar">
    <div>
      <div class="title"><span class="dot"></span>BTC/USDT 1-Year Backtest Report</div>
      <div class="sub">Interval: 30m | Source: Binance OHLCV</div>
    </div>
    <button id="themeToggle" style="background: var(--line); border: 1px solid var(--line); color: var(--text); border-radius: 4px; padding: 6px 12px; cursor: pointer; font-size: 11px; font-weight: 600;">☀️ Light Mode</button>
  </div>

  <div class="grid6">
    <div class="card">
      <h3>Net Profit</h3>
      <div class="v __NET_PROFIT_CLASS__">__NET_PROFIT_STR__</div>
    </div>
    <div class="card">
      <h3>Win Rate</h3>
      <div class="v">__WIN_RATE__%</div>
    </div>
    <div class="card">
      <h3>Max Drawdown</h3>
      <div class="v neg">-__MAX_DD__%</div>
    </div>
    <div class="card">
      <h3>Max Profit</h3>
      <div class="v pos">+__MAX_PROFIT_STR__</div>
    </div>
    <div class="card">
      <h3>Max Loss</h3>
      <div class="v neg">__MAX_LOSS_STR__</div>
    </div>
    <div class="card">
      <h3>Total Trades</h3>
      <div class="v">__TOTAL_TRADES__</div>
    </div>
  </div>

  <div class="eq-card">
    <h3>Equity Curve (Starting Capital: $10,000)</h3>
    <canvas id="eqCanvas" height="320"></canvas>
  </div>

  <div class="split-grid">
    <div class="table-card">
      <div class="table-head">
        <h3>Monthly Performance (USD)</h3>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Month</th>
              <th class="num">Net P&amp;L</th>
            </tr>
          </thead>
          <tbody>
            __MONTHLY_ROWS__
          </tbody>
        </table>
      </div>
    </div>

    <div class="table-card">
      <div class="table-head">
        <h3>Backtest Statistics</h3>
      </div>
      <div class="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th class="num">Value</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Profit Factor</td>
              <td class="num">__PROFIT_FACTOR__</td>
            </tr>
            <tr>
              <td>Winning Trades</td>
              <td class="num pos">__WINS_COUNT__</td>
            </tr>
            <tr>
              <td>Losing Trades</td>
              <td class="num neg">__LOSSES_COUNT__</td>
            </tr>
            <tr>
              <td>Average Winning Trade</td>
              <td class="num pos">+__AVG_WIN__</td>
            </tr>
            <tr>
              <td>Average Losing Trade</td>
              <td class="num neg">-__AVG_LOSS__</td>
            </tr>
            <tr>
              <td>Starting Capital</td>
              <td class="num">$10,000.00</td>
            </tr>
            <tr>
              <td>Ending Capital</td>
              <td class="num">__ENDING_CAP__</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="table-card" style="margin-top: 14px;">
    <div class="table-head">
      <h3>Backtest Trade Log History</h3>
    </div>
    <div class="table-scroll" style="max-height: 500px; overflow-x: auto;">
      <table style="min-width: 900px;">
        <thead>
          <tr>
            <th>#</th>
            <th>Date</th>
            <th>Entry Time</th>
            <th>Entry Price</th>
            <th>Exit Time</th>
            <th>Exit Price</th>
            <th>Points Captured</th>
            <th class="num">Realized P&amp;L</th>
            <th>Exit Reason</th>
          </tr>
        </thead>
        <tbody>
          __TRADE_ROWS__
        </tbody>
      </table>
    </div>
  </div>
</div>

<script>
const trades = __TRADES_JSON_STR__;

function fmtMoney(v) {
  return (v >= 0 ? '+' : '') + '$' + Number(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function drawEquityCurve() {
  const canvas = document.getElementById('eqCanvas');
  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const container = canvas.parentElement;
  const w = container.clientWidth - 32;
  const h = window.innerWidth <= 600 ? 220 : 320;
  canvas.width = w * dpr; canvas.height = h * dpr;
  canvas.style.width = w + 'px'; canvas.style.height = h + 'px';
  ctx.scale(dpr, dpr);

  const startingCap = 10000.0;
  const points = [startingCap];
  trades.forEach(t => points.push(t.equity));

  const min = Math.min(...points), max = Math.max(...points);
  const range = (max - min) || 1;
  const pad = 20;
  const stepX = (w - pad * 2) / Math.max(points.length - 1, 1);
  const toY = v => h - pad - ((v - min) / range) * (h - pad * 2);

  function drawChart(hoverIdx = -1) {
    ctx.clearRect(0, 0, w, h);
    
    // Grid lines
    ctx.strokeStyle = 'var(--line)';
    ctx.lineWidth = 0.5;
    ctx.setLineDash([4, 4]);
    for (let i = 1; i < 4; i++) {
      const y = pad + (i * (h - pad * 2)) / 4;
      ctx.beginPath();
      ctx.moveTo(pad, y);
      ctx.lineTo(w - pad, y);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Gradient fill
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(62, 207, 142, 0.15)');
    grad.addColorStop(1, 'rgba(62, 207, 142, 0.0)');

    ctx.beginPath();
    points.forEach((v, i) => {
      const x = pad + i * stepX;
      const y = toY(v);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.lineTo(pad + (points.length - 1) * stepX, h - pad);
    ctx.lineTo(pad, h - pad);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Main line
    ctx.beginPath();
    points.forEach((v, i) => {
      const x = pad + i * stepX;
      const y = toY(v);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.strokeStyle = 'var(--green)';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Hover line
    if (hoverIdx >= 0 && hoverIdx < points.length) {
      const x = pad + hoverIdx * stepX;
      const y = toY(points[hoverIdx]);

      ctx.strokeStyle = 'var(--dim)';
      ctx.lineWidth = 1;
      ctx.setLineDash([2, 2]);
      ctx.beginPath();
      ctx.moveTo(x, pad);
      ctx.lineTo(x, h - pad);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.beginPath();
      ctx.arc(x, y, 6, 0, Math.PI * 2);
      ctx.fillStyle = 'var(--green)';
      ctx.strokeStyle = 'var(--panel)';
      ctx.lineWidth = 2;
      ctx.fill();
      ctx.stroke();

      const tooltipText = hoverIdx === 0 ? `Starting: $10,000.00` : `Trade #${hoverIdx}: ${fmtMoney(points[hoverIdx])}`;
      ctx.font = '11px sans-serif';
      const textWidth = ctx.measureText(tooltipText).width;
      const boxW = textWidth + 16;
      const boxH = 24;
      let boxX = x + 10;
      if (boxX + boxW > w) boxX = x - boxW - 10;
      let boxY = y - 12;
      if (boxY < pad) boxY = pad;

      ctx.fillStyle = 'var(--panel)';
      ctx.strokeStyle = 'var(--line)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      if (ctx.roundRect) {
        ctx.roundRect(boxX, boxY, boxW, boxH, 4);
      } else {
        ctx.rect(boxX, boxY, boxW, boxH);
      }
      ctx.fill();
      ctx.stroke();

      ctx.fillStyle = 'var(--text)';
      ctx.fillText(tooltipText, boxX + 8, boxY + 16);
    }
  }

  drawChart();

  canvas.onmousemove = (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const hoverIdx = Math.round((mouseX - pad) / stepX);
    if (hoverIdx >= 0 && hoverIdx < points.length) {
      drawChart(hoverIdx);
    }
  };
  canvas.onmouseleave = () => {
    drawChart();
  };
}

// Theme Toggle Script
const toggleBtn = document.getElementById('themeToggle');
toggleBtn.addEventListener('click', () => {
  document.body.classList.toggle('light');
  const isLight = document.body.classList.contains('light');
  toggleBtn.textContent = isLight ? '🌙 Dark Mode' : '☀️ Light Mode';
  localStorage.setItem('theme', isLight ? 'light' : 'dark');
});
if (localStorage.getItem('theme') === 'light') {
  document.body.classList.add('light');
  toggleBtn.textContent = '🌙 Dark Mode';
}

drawEquityCurve();
window.addEventListener('resize', () => drawEquityCurve());
</script>
</body>
</html>
"""

    # Populate monthly P/L rows
    monthly_rows = ""
    for r in monthly_pl_list:
        pnl = r["real_pl"]
        cls = "pos" if pnl > 0 else ("neg" if pnl < 0 else "")
        sign = "+" if pnl > 0 else ""
        monthly_rows += f"""            <tr>
              <td>{r['month']}</td>
              <td class="num {cls}">{sign}${pnl:,.2f}</td>
            </tr>\n"""

    # Populate trade rows
    trade_rows = ""
    for t in reversed(trades_json): # latest first in table
        pnl = t["real_pl"]
        pnl_cls = "pos" if pnl > 0 else ("neg" if pnl < 0 else "")
        sign = "+" if pnl > 0 else ""
        
        date_str = t["entry_time"].split(" ")[0]
        entry_time_only = t["entry_time"].split(" ")[1]
        exit_time_only = t["exit_time"].split(" ")[1]
        
        trade_rows += f"""            <tr>
              <td>#{t['id']}</td>
              <td>{date_str}</td>
              <td>{entry_time_only}</td>
              <td>{t['entry_price']:.2f}</td>
              <td>{exit_time_only}</td>
              <td>{t['exit_price']:.2f}</td>
              <td class="{pnl_cls}">{"+" if t['points_captured'] > 0 else ""}{t['points_captured']:.2f}</td>
              <td class="num {pnl_cls}">{sign}${pnl:,.2f}</td>
              <td>{t['exit_reason']}</td>
            </tr>\n"""

    net_profit_class = "pos" if total_profit > 0 else ("neg" if total_profit < 0 else "")
    net_profit_str = f"+${total_profit:,.2f}" if total_profit >= 0 else f"-${abs(total_profit):,.2f}"
    max_profit_str = f"${max_profit:,.2f}"
    max_loss_str = f"-${abs(max_loss):,.2f}" if max_loss < 0 else f"${max_loss:,.2f}"
    ending_cap = starting_cap + total_profit

    rendered = html_template.replace("__NET_PROFIT_CLASS__", net_profit_class)
    rendered = rendered.replace("__NET_PROFIT_STR__", net_profit_str)
    rendered = rendered.replace("__WIN_RATE__", f"{win_rate:.2f}")
    rendered = rendered.replace("__MAX_DD__", f"{max_dd:.2f}")
    rendered = rendered.replace("__MAX_PROFIT_STR__", max_profit_str)
    rendered = rendered.replace("__MAX_LOSS_STR__", max_loss_str)
    rendered = rendered.replace("__TOTAL_TRADES__", str(total_trades))
    rendered = rendered.replace("__MONTHLY_ROWS__", monthly_rows)
    rendered = rendered.replace("__TRADE_ROWS__", trade_rows)
    rendered = rendered.replace("__PROFIT_FACTOR__", f"{profit_factor:.2f}")
    rendered = rendered.replace("__WINS_COUNT__", str(len(wins)))
    rendered = rendered.replace("__LOSSES_COUNT__", str(len(losses)))
    rendered = rendered.replace("__AVG_WIN__", f"${abs(avg_win):,.2f}")
    rendered = rendered.replace("__AVG_LOSS__", f"${abs(avg_loss):,.2f}")
    rendered = rendered.replace("__ENDING_CAP__", f"${ending_cap:,.2f}")
    rendered = rendered.replace("__TRADES_JSON_STR__", json.dumps(trades_json))

    out_html = os.path.join("dashboard", "backtest_report.html")
    os.makedirs("dashboard", exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(rendered)
    print(f"Generated backtest report HTML -> {out_html}")

if __name__ == "__main__":
    generate_report()
