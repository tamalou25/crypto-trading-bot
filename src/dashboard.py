from flask import Flask, render_template_string, jsonify
from datetime import datetime
import threading

app = Flask(__name__)

_portfolio = None
_exchange = None
_pnl_history = []
_price_history = {}

HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="2">
<title>AI Crypto Trading Bot</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:#0a0e1a; color:#e0e0e0; font-family:'Courier New',monospace; }
  .header { background:linear-gradient(90deg,#0d1b2a,#1a2f4e); padding:16px 24px;
    border-bottom:2px solid #00d4ff; display:flex; justify-content:space-between; align-items:center; }
  .header h1 { color:#00d4ff; font-size:1.4em; letter-spacing:2px; }
  .badge { background:#ff4444; color:#fff; padding:4px 12px; border-radius:20px; font-size:.75em; }
  .badge.paper { background:#f5a623; }
  .grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; padding:16px; }
  .grid2 { display:grid; grid-template-columns:1fr 1fr; gap:12px; padding:0 16px 16px; }
  .grid3 { display:grid; grid-template-columns:2fr 1fr; gap:12px; padding:0 16px 16px; }
  .card { background:#111827; border:1px solid #1f2d40; border-radius:10px; padding:16px; }
  .card h3 { color:#00d4ff; font-size:.8em; letter-spacing:1px; margin-bottom:10px; border-bottom:1px solid #1f2d40; padding-bottom:6px; }
  .stat-val { font-size:1.8em; font-weight:bold; }
  .stat-sub { font-size:.75em; color:#888; margin-top:4px; }
  .green { color:#00ff88; } .red { color:#ff4444; } .yellow { color:#f5a623; } .blue { color:#00d4ff; }
  table { width:100%; border-collapse:collapse; font-size:.82em; }
  th { color:#00d4ff; text-align:left; padding:6px 8px; border-bottom:1px solid #1f2d40; font-weight:normal; letter-spacing:1px; }
  td { padding:6px 8px; border-bottom:1px solid #0d1520; }
  tr:hover { background:#0d1b2a; }
  .tag { display:inline-block; padding:2px 8px; border-radius:10px; font-size:.72em; font-weight:bold; }
  .tag-long { background:#00ff8822; color:#00ff88; border:1px solid #00ff88; }
  .tag-short { background:#ff444422; color:#ff4444; border:1px solid #ff4444; }
  .tag-hold { background:#f5a62322; color:#f5a623; border:1px solid #f5a623; }
  .progress { background:#1f2d40; border-radius:4px; height:6px; margin-top:6px; }
  .progress-bar { height:6px; border-radius:4px; transition:width .5s; }
  .ticker { display:flex; gap:24px; padding:10px 24px; background:#0d1520; border-bottom:1px solid #1f2d40;
    overflow:hidden; font-size:.82em; }
  .tick-item { white-space:nowrap; }
  canvas { max-height:220px; }
  .log-box { height:180px; overflow-y:auto; font-size:.78em; }
  .log-entry { padding:3px 0; border-bottom:1px solid #0d1520; }
  .signal-bar { display:flex; gap:6px; margin-top:8px; }
  .signal-item { flex:1; text-align:center; padding:6px; border-radius:6px; font-size:.75em; }
</style>
</head>
<body>
<div class="header">
  <h1>&#127916; AI CRYPTO TRADING BOT</h1>
  <div style="display:flex;gap:12px;align-items:center">
    <span id="clock" style="color:#888;font-size:.85em"></span>
    <span class="badge paper">PAPER MODE</span>
    <span class="badge" style="background:#00aa44">LIVE</span>
  </div>
</div>

<!-- TICKER -->
<div class="ticker" id="ticker">Chargement des prix...</div>

<!-- STATS -->
<div class="grid" id="stats-grid">
  <div class="card"><h3>CAPITAL TOTAL</h3><div class="stat-val blue" id="s-total">--</div><div class="stat-sub" id="s-roi">ROI: --</div></div>
  <div class="card"><h3>PNL REALISE</h3><div class="stat-val" id="s-pnl">--</div><div class="stat-sub" id="s-trades">-- trades</div></div>
  <div class="card"><h3>WIN RATE</h3><div class="stat-val" id="s-wr">--%</div>
    <div class="progress"><div class="progress-bar green" id="s-wr-bar" style="width:0%"></div></div>
    <div class="stat-sub" id="s-wrsub">-- gagnants / -- perdants</div>
  </div>
  <div class="card"><h3>POSITIONS</h3><div class="stat-val yellow" id="s-pos">--</div><div class="stat-sub" id="s-cash">Cash: -- USDT</div></div>
</div>

<!-- CHARTS -->
<div class="grid2">
  <div class="card">
    <h3>COURBE PNL (temps reel)</h3>
    <canvas id="pnlChart"></canvas>
  </div>
  <div class="card">
    <h3>REPARTITION CAPITAL</h3>
    <canvas id="allocChart"></canvas>
  </div>
</div>

<!-- MARCHE + POSITIONS -->
<div class="grid3">
  <div class="card">
    <h3>MARCHE EN DIRECT</h3>
    <table>
      <tr><th>Paire</th><th>Prix</th><th>1m%</th><th>Haut</th><th>Bas</th><th>Volume</th><th>Signal</th><th>Force</th></tr>
      <tbody id="market-rows"></tbody>
    </table>
  </div>
  <div class="card">
    <h3>INDICATEURS TECHNIQUES</h3>
    <div id="indicators"></div>
  </div>
</div>

<!-- POSITIONS + TRADES -->
<div class="grid2">
  <div class="card">
    <h3>POSITIONS OUVERTES</h3>
    <table>
      <tr><th>Paire</th><th>Type</th><th>Entree</th><th>Actuel</th><th>PnL</th><th>PnL%</th><th>SL</th><th>TP</th></tr>
      <tbody id="pos-rows"></tbody>
    </table>
  </div>
  <div class="card">
    <h3>DERNIERS TRADES</h3>
    <table>
      <tr><th>Paire</th><th>Type</th><th>Entree</th><th>Sortie</th><th>PnL</th><th>%</th><th>Heure</th></tr>
      <tbody id="trade-rows"></tbody>
    </table>
  </div>
</div>

<!-- STATS AVANCEES + LOG -->
<div class="grid2" style="padding-bottom:24px">
  <div class="card">
    <h3>STATISTIQUES AVANCEES</h3>
    <table><tbody id="adv-stats"></tbody></table>
  </div>
  <div class="card">
    <h3>ACTIVITE EN DIRECT</h3>
    <div class="log-box" id="log-box"></div>
  </div>
</div>

<script>
let pnlChart, allocChart;
let pnlLabels = [], pnlData = [];

function initCharts() {
  const ctx1 = document.getElementById('pnlChart').getContext('2d');
  pnlChart = new Chart(ctx1, {
    type: 'line',
    data: { labels: pnlLabels, datasets: [{
      label: 'PnL (USDT)', data: pnlData,
      borderColor: '#00d4ff', backgroundColor: 'rgba(0,212,255,0.08)',
      borderWidth: 2, pointRadius: 0, fill: true, tension: 0.4
    }]},
    options: { responsive:true, animation:false, plugins:{legend:{display:false}},
      scales: { x:{display:false}, y:{ grid:{color:'#1f2d40'}, ticks:{color:'#888',
        callback: v => (v>=0?'+':'')+v.toFixed(2)+' $'} } } }
  });

  const ctx2 = document.getElementById('allocChart').getContext('2d');
  allocChart = new Chart(ctx2, {
    type: 'doughnut',
    data: { labels: ['Cash'], datasets: [{ data: [100],
      backgroundColor: ['#00d4ff','#00ff88','#ff4444','#f5a623','#aa44ff','#ff88aa'],
      borderWidth: 0 }]},
    options: { responsive:true, animation:false,
      plugins: { legend: { position:'bottom', labels:{color:'#888',font:{size:10}} } } }
  });
}

function fmt(v, dec=2) { return v >= 0 ? '+'+v.toFixed(dec) : v.toFixed(dec); }
function colorClass(v) { return v >= 0 ? 'green' : 'red'; }

function update() {
  fetch('/api/data').then(r=>r.json()).then(d => {
    // Clock
    document.getElementById('clock').textContent = new Date().toLocaleTimeString();

    // Ticker
    let ticker = '';
    for (const [pair, info] of Object.entries(d.market)) {
      const c = info.change_1m >= 0 ? '#00ff88' : '#ff4444';
      const arr = info.change_1m >= 0 ? '▲' : '▼';
      ticker += `<span class="tick-item"><b>${pair}</b> <span style="color:${c}">${arr} ${info.price.toFixed(2)} (${fmt(info.change_1m,2)}%)</span></span>`;
    }
    document.getElementById('ticker').innerHTML = ticker || 'Chargement...';

    // Stats
    const p = d.portfolio;
    document.getElementById('s-total').textContent = p.total.toFixed(2) + ' USDT';
    document.getElementById('s-total').className = 'stat-val ' + colorClass(p.pnl);
    document.getElementById('s-roi').textContent = `ROI: ${fmt(p.roi,2)}% | Initial: ${p.initial.toFixed(0)} USDT`;
    document.getElementById('s-pnl').textContent = fmt(p.pnl,2) + ' USDT';
    document.getElementById('s-pnl').className = 'stat-val ' + colorClass(p.pnl);
    document.getElementById('s-trades').textContent = `${p.total_trades} trades | ${p.cycles} cycles`;
    document.getElementById('s-wr').textContent = p.win_rate.toFixed(1) + '%';
    document.getElementById('s-wr').className = 'stat-val ' + (p.win_rate >= 50 ? 'green' : 'red');
    document.getElementById('s-wr-bar').style.width = p.win_rate + '%';
    document.getElementById('s-wrsub').textContent = `${p.wins} gagnants / ${p.losses} perdants`;
    document.getElementById('s-pos').textContent = Object.keys(p.positions).length + ' positions';
    document.getElementById('s-cash').textContent = `Cash: ${p.cash.toFixed(2)} USDT | En jeu: ${p.in_position.toFixed(2)} USDT`;

    // PnL chart
    const t = new Date().toLocaleTimeString();
    pnlLabels.push(t); pnlData.push(p.pnl);
    if (pnlLabels.length > 120) { pnlLabels.shift(); pnlData.shift(); }
    pnlChart.update();

    // Alloc chart
    const allocLabels = ['Cash'];
    const allocData = [p.cash];
    for (const [sym, pos] of Object.entries(p.positions)) {
      allocLabels.push(sym);
      allocData.push(pos.current_value);
    }
    allocChart.data.labels = allocLabels;
    allocChart.data.datasets[0].data = allocData;
    allocChart.update();

    // Market table
    let mRows = '';
    for (const [pair, info] of Object.entries(d.market)) {
      const cc = info.change_1m >= 0 ? 'green' : 'red';
      const arr = info.change_1m >= 0 ? '▲' : '▼';
      const sigTag = info.signal === 'BUY' ? 'tag-long' : info.signal === 'SELL' ? 'tag-short' : 'tag-hold';
      const sigLabel = info.signal === 'BUY' ? 'LONG' : info.signal === 'SELL' ? 'SHORT' : 'HOLD';
      const strength = (info.strength * 100).toFixed(0);
      mRows += `<tr>
        <td><b>${arr} ${pair}</b></td>
        <td class="${cc}">${info.price.toFixed(2)}</td>
        <td class="${cc}">${fmt(info.change_1m,2)}%</td>
        <td>${info.high.toFixed(2)}</td>
        <td>${info.low.toFixed(2)}</td>
        <td>${info.volume.toFixed(0)}</td>
        <td><span class="tag ${sigTag}">${sigLabel}</span></td>
        <td><div class="progress"><div class="progress-bar ${cc}" style="width:${strength}%"></div></div></td>
      </tr>`;
    }
    document.getElementById('market-rows').innerHTML = mRows || '<tr><td colspan="8" style="color:#888">Chargement...</td></tr>';

    // Indicators
    let indHTML = '';
    for (const [pair, ind] of Object.entries(d.indicators)) {
      const rsiC = ind.rsi > 70 ? 'red' : ind.rsi < 30 ? 'green' : 'yellow';
      indHTML += `<div style="margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #1f2d40">
        <div style="color:#00d4ff;font-size:.8em;margin-bottom:4px">${pair}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:.76em">
          <span>RSI: <b class="${rsiC}">${ind.rsi.toFixed(1)}</b></span>
          <span>MACD: <b class="${ind.macd >= 0 ? 'green':'red'}">${ind.macd.toFixed(2)}</b></span>
          <span>ADX: <b class="${ind.adx > 25 ? 'green':'yellow'}">${ind.adx.toFixed(1)}</b></span>
          <span>BB%: <b>${(ind.bb_pct*100).toFixed(0)}%</b></span>
        </div>
      </div>`;
    }
    document.getElementById('indicators').innerHTML = indHTML || '<span style="color:#888">Chargement...</span>';

    // Positions
    let pRows = '';
    for (const [sym, pos] of Object.entries(p.positions)) {
      const pc = pos.pnl >= 0 ? 'green' : 'red';
      const typeTag = pos.type === 'short' ? 'tag-short' : 'tag-long';
      const typeLabel = pos.type === 'short' ? 'SHORT' : 'LONG';
      pRows += `<tr>
        <td><b>${sym}</b></td>
        <td><span class="tag ${typeTag}">${typeLabel}</span></td>
        <td>${pos.entry.toFixed(2)}</td>
        <td class="${pc}">${pos.current.toFixed(2)}</td>
        <td class="${pc}">${fmt(pos.pnl,2)}</td>
        <td class="${pc}">${fmt(pos.pnl_pct,2)}%</td>
        <td class="red">${pos.sl.toFixed(2)}</td>
        <td class="green">${pos.tp.toFixed(2)}</td>
      </tr>`;
    }
    document.getElementById('pos-rows').innerHTML = pRows || '<tr><td colspan="8" style="color:#888">Aucune position ouverte</td></tr>';

    // Trades
    let tRows = '';
    for (const t of d.trades.slice(-8).reverse()) {
      const tc = t.pnl >= 0 ? 'green' : 'red';
      const typeTag = t.type === 'short' ? 'tag-short' : 'tag-long';
      tRows += `<tr>
        <td><b>${t.symbol}</b></td>
        <td><span class="tag ${typeTag}">${t.type === 'short' ? 'SHORT':'LONG'}</span></td>
        <td>${t.entry.toFixed(2)}</td>
        <td>${t.exit.toFixed(2)}</td>
        <td class="${tc}">${fmt(t.pnl,2)}</td>
        <td class="${tc}">${fmt(t.pnl_pct,2)}%</td>
        <td style="color:#888">${t.time}</td>
      </tr>`;
    }
    document.getElementById('trade-rows').innerHTML = tRows || '<tr><td colspan="7" style="color:#888">Aucun trade</td></tr>';

    // Advanced stats
    const s = d.stats;
    const rows = [
      ['Profit moyen / trade', fmt(s.avg_pnl,2) + ' USDT'],
      ['Meilleur trade', '+' + s.best_trade.toFixed(2) + ' USDT'],
      ['Pire trade', s.worst_trade.toFixed(2) + ' USDT'],
      ['Max Drawdown', s.max_drawdown.toFixed(2) + '%'],
      ['Profit Factor', s.profit_factor.toFixed(2)],
      ['Sharpe Ratio (est.)', s.sharpe.toFixed(2)],
      ['Total investi', s.total_invested.toFixed(2) + ' USDT'],
      ['Duree moyenne trade', s.avg_duration],
    ];
    document.getElementById('adv-stats').innerHTML = rows.map(([k,v]) =>
      `<tr><td style="color:#888">${k}</td><td style="text-align:right;color:#e0e0e0">${v}</td></tr>`
    ).join('');

    // Log
    const logBox = document.getElementById('log-box');
    logBox.innerHTML = d.log.slice(-20).reverse().map(l =>
      `<div class="log-entry">${l}</div>`
    ).join('');
  }).catch(e => console.log('Erreur API:', e));
}

document.addEventListener('DOMContentLoaded', () => {
  initCharts();
  update();
  setInterval(update, 1000);
});
</script>
</body></html>
'''

@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/data')
def api_data():
    if not _portfolio:
        return jsonify({})
    
    p = _portfolio
    
    # Prix live depuis exchange
    market = {}
    indicators = {}
    try:
        from src.strategy import TradingStrategy
        import ta
        pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
        strat = TradingStrategy()
        for pair in pairs:
            ohlcv = _exchange.get_ohlcv(pair, timeframe='1m', limit=50)
            if ohlcv is not None and len(ohlcv) >= 20:
                ohlcv2 = strat.compute_indicators(ohlcv.copy())
                ohlcv2.dropna(inplace=True)
                if len(ohlcv2) < 2:
                    continue
                last = ohlcv2.iloc[-1]
                signal_data = strat.generate_signal(ohlcv, pair)
                market[pair] = {
                    'price': float(last['close']),
                    'open': float(last['open']),
                    'high': float(last['high']),
                    'low': float(last['low']),
                    'volume': float(last['volume']),
                    'change_1m': float((last['close'] - last['open']) / last['open'] * 100),
                    'signal': signal_data['action'],
                    'strength': float(signal_data['confidence'])
                }
                indicators[pair] = {
                    'rsi': float(last.get('rsi', 50)),
                    'macd': float(last.get('macd_hist', 0)),
                    'adx': float(last.get('adx', 0)),
                    'bb_pct': float(last.get('bb_pct', 0.5))
                }
    except Exception as e:
        pass
    
    # Portfolio
    positions_value = 0
    positions_out = {}
    for sym, pos in p.positions.items():
        curr = market.get(sym, {}).get('price', pos['entry_price'])
        pnl = (curr - pos['entry_price']) * pos['amount']
        pnl_pct = (curr - pos['entry_price']) / pos['entry_price'] * 100
        val = curr * pos['amount']
        positions_value += val
        positions_out[sym] = {
            'entry': pos['entry_price'], 'current': curr,
            'amount': pos['amount'], 'pnl': pnl, 'pnl_pct': pnl_pct,
            'current_value': val,
            'sl': pos['entry_price'] * 0.90,
            'tp': pos['entry_price'] * 1.20,
            'type': pos.get('trade_type', 'long')
        }
    
    total = p.cash + positions_value
    pnl_total = total - p.initial_capital
    roi = pnl_total / p.initial_capital * 100
    wins = sum(1 for t in p.trade_history if t['pnl'] > 0)
    losses = len(p.trade_history) - wins
    win_rate = (wins / len(p.trade_history) * 100) if p.trade_history else 0
    
    # Stats avancees
    pnls = [t['pnl'] for t in p.trade_history]
    best = max(pnls) if pnls else 0
    worst = min(pnls) if pnls else 0
    avg_pnl = sum(pnls) / len(pnls) if pnls else 0
    gains = sum(x for x in pnls if x > 0)
    loss_sum = abs(sum(x for x in pnls if x < 0))
    profit_factor = gains / loss_sum if loss_sum > 0 else 0
    import statistics
    sharpe = statistics.mean(pnls) / statistics.stdev(pnls) if len(pnls) > 2 else 0
    total_invested = sum(pos['cost'] for pos in p.positions.values())
    
    # Trades output
    trades_out = []
    for t in p.trade_history:
        trades_out.append({
            'symbol': t['symbol'],
            'entry': t['entry_price'],
            'exit': t['exit_price'],
            'pnl': t['pnl'],
            'pnl_pct': t['pnl_pct'],
            'time': t['exit_time'].strftime('%H:%M:%S') if 'exit_time' in t else '--',
            'type': t.get('trade_type', 'long')
        })
    
    return jsonify({
        'portfolio': {
            'total': total, 'cash': p.cash, 'pnl': pnl_total,
            'roi': roi, 'initial': p.initial_capital,
            'in_position': positions_value,
            'total_trades': len(p.trade_history),
            'wins': wins, 'losses': losses, 'win_rate': win_rate,
            'positions': positions_out,
            'cycles': getattr(p, 'cycles', 0)
        },
        'market': market,
        'indicators': indicators,
        'trades': trades_out,
        'stats': {
            'avg_pnl': avg_pnl, 'best_trade': best, 'worst_trade': worst,
            'max_drawdown': 0, 'profit_factor': profit_factor,
            'sharpe': sharpe, 'total_invested': total_invested,
            'avg_duration': 'N/A'
        },
        'log': getattr(p, 'activity_log', [])
    })

def run_dashboard(portfolio, exchange):
    global _portfolio, _exchange
    _portfolio = portfolio
    _exchange = exchange
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
