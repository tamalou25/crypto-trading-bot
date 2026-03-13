from flask import Flask, render_template_string, jsonify
from datetime import datetime
import threading, time, statistics

app = Flask(__name__)
_portfolio = None
_exchange  = None
_cache = {'market': {}, 'indicators': {}, 'analysis': {}, 'last_update': '--'}

# ─── Thread cache marche ────────────────────────────────────────────────────
def _update_cache():
    while True:
        try:
            if _exchange is None:
                time.sleep(2); continue
            from src.strategy import TradingStrategy
            strat = TradingStrategy()
            strat.set_exchange(_exchange)
            for pair in ['BTC/USDT','ETH/USDT','SOL/USDT','BNB/USDT']:
                try:
                    ohlcv = _exchange.get_ohlcv(pair, timeframe='1m', limit=200)
                    if ohlcv is None or len(ohlcv) < 30: continue
                    sig = strat.generate_signal(ohlcv.copy(), pair)
                    last = ohlcv.iloc[-1]; prev = ohlcv.iloc[-2]
                    ch = float((last['close']-prev['close'])/prev['close']*100)
                    _cache['market'][pair] = {
                        'price':float(last['close']), 'high':float(last['high']),
                        'low':float(last['low']),    'volume':float(last['volume']),
                        'change_1m':ch, 'signal':sig['action'],
                        'strength':float(sig['confidence']),
                        'score':float(sig.get('total_score',0))
                    }
                    _cache['indicators'][pair] = {
                        'rsi':float(sig.get('rsi',50)),
                        'adx':float(sig.get('adx',0)),
                        'bb_pct':float(sig.get('bb_pct',0.5)),
                        'macd':float(sig.get('momentum_score',0))
                    }
                    _cache['analysis'][pair] = {
                        'action':sig['action'],
                        'confidence':float(sig['confidence']),
                        'total_score':float(sig.get('total_score',0)),
                        'trend_score':float(sig.get('trend_score',0)),
                        'momentum_score':float(sig.get('momentum_score',0)),
                        'volume_score':float(sig.get('volume_score',0)),
                        'pattern_score':float(sig.get('pattern_score',0)),
                        'mtf_score':float(sig.get('mtf_score',0)),
                        'signals':[str(s) for s in sig.get('signals',[])[:6]],
                        'patterns':[str(s) for s in sig.get('patterns',[])]
                    }
                except Exception as e:
                    pass
            _cache['last_update'] = datetime.now().strftime('%H:%M:%S')
        except: pass
        time.sleep(3)

# ─── HTML / JS dashboard ────────────────────────────────────────────────────
HTML = r'''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>AI Crypto Bot Pro</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#060b14;color:#c8d4e0;font-family:"Segoe UI",sans-serif;font-size:13px;line-height:1.4}
/* layout */
.hd{background:linear-gradient(90deg,#07101e,#0d1f35);padding:11px 18px;border-bottom:2px solid #00d4ff33;display:flex;justify-content:space-between;align-items:center}
.hd h1{color:#00d4ff;font-size:1.05em;letter-spacing:3px;font-weight:600}
.tk{display:flex;gap:16px;padding:6px 18px;background:#070e1a;border-bottom:1px solid #0e1e2e;font-size:.79em;flex-wrap:wrap}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:10px 10px 0}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:8px 10px 0}
.g3{display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;padding:8px 10px 0}
.g21{display:grid;grid-template-columns:2fr 1fr;gap:8px;padding:8px 10px 0}
.pb{padding-bottom:16px}
.card{background:#0c1520;border:1px solid #162030;border-radius:8px;padding:12px}
.card h3{color:#00aacc;font-size:.7em;letter-spacing:1.5px;margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid #162030;text-transform:uppercase}
/* typography */
.big{font-size:1.85em;font-weight:700;margin:2px 0}
.sub{font-size:.72em;color:#4a5c70;margin-top:3px}
.g{color:#00e87a}.r{color:#ff4455}.y{color:#f5a623}.b{color:#00d4ff}.w{color:#c8d4e0}
.dim{color:#4a5c70}
/* badge */
.badge{padding:2px 8px;border-radius:8px;font-size:.68em;font-weight:700;display:inline-flex;align-items:center;gap:4px}
.bdg-paper{background:#f5a62318;color:#f5a623;border:1px solid #f5a62340}
.bdg-live{background:#00e87a18;color:#00e87a;border:1px solid #00e87a40}
.dot{width:6px;height:6px;border-radius:50%;background:#00e87a;animation:pulse 1.5s infinite}
@keyframes pulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.4;transform:scale(.8)}}
/* table */
table{width:100%;border-collapse:collapse;font-size:.78em}
th{color:#2a4a6a;text-align:left;padding:4px 7px;border-bottom:1px solid #0e1e2e;font-weight:500;font-size:.72em;letter-spacing:.4px;text-transform:uppercase;white-space:nowrap}
td{padding:5px 7px;border-bottom:1px solid #0a1520;white-space:nowrap;vertical-align:middle}
tr:hover td{background:#0d1f3520}
/* tags */
.tag{display:inline-block;padding:1px 6px;border-radius:5px;font-size:.68em;font-weight:700;white-space:nowrap}
.tl{background:#00e87a14;color:#00e87a;border:1px solid #00e87a33}
.ts{background:#ff445514;color:#ff4455;border:1px solid #ff445533}
.th{background:#f5a62314;color:#f5a623;border:1px solid #f5a62333}
/* bars */
.bw{background:#0e1e2e;border-radius:3px;height:4px}
.bf{height:4px;border-radius:3px;transition:width .5s}
/* score bars */
.sb{display:flex;align-items:center;gap:6px;margin:3px 0;font-size:.74em}
.sb-lbl{width:82px;color:#4a5c70;flex-shrink:0;font-size:.95em}
.sb-val{width:36px;text-align:right;font-weight:600}
.sb-bar{flex:1}
/* log */
.log{height:140px;overflow-y:auto;font-size:.73em}
.ll{padding:2px 0;border-bottom:1px solid #0a1520;color:#3a4f63}
/* ind */
.ig{display:grid;grid-template-columns:1fr 1fr;gap:2px;font-size:.73em;margin-top:3px}
.il{color:#3a4f63}
/* scrollbar */
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:#07101e}::-webkit-scrollbar-thumb{background:#162030;border-radius:2px}
</style>
</head>
<body>

<!-- HEADER -->
<div class="hd">
  <h1>&#9889; AI CRYPTO TRADING BOT PRO</h1>
  <div style="display:flex;gap:8px;align-items:center">
    <span id="clock" class="dim" style="font-size:.82em"></span>
    <span class="badge bdg-paper">PAPER</span>
    <span class="badge bdg-live"><span class="dot"></span>LIVE</span>
  </div>
</div>

<!-- TICKER -->
<div class="tk" id="ticker"><span class="dim">Chargement...</span></div>

<!-- KPI CARDS -->
<div class="g4">
  <div class="card">
    <h3>Capital Total</h3>
    <div class="big b" id="k-tot">--</div>
    <div class="sub" id="k-roi">ROI: --</div>
  </div>
  <div class="card">
    <h3>PnL Unrealise</h3>
    <div class="big" id="k-pnl">--</div>
    <div class="sub" id="k-trades">0 trades</div>
  </div>
  <div class="card">
    <h3>Win Rate</h3>
    <div class="big" id="k-wr">--%</div>
    <div class="bw" style="margin-top:5px"><div class="bf g" id="k-wrb" style="width:0%"></div></div>
    <div class="sub" id="k-wrs">0W / 0L</div>
  </div>
  <div class="card">
    <h3>Positions / Cash</h3>
    <div class="big y" id="k-pos">0</div>
    <div class="sub" id="k-cash">Cash: --</div>
  </div>
</div>

<!-- CHARTS -->
<div class="g2" style="padding-top:8px">
  <div class="card">
    <h3>Courbe PnL (temps reel — vert=profit / rouge=perte)</h3>
    <canvas id="pnlC" height="90"></canvas>
  </div>
  <div class="card">
    <h3>Repartition Capital</h3>
    <canvas id="allocC" height="90"></canvas>
  </div>
</div>

<!-- MARCHE + INDICATEURS -->
<div class="g21" style="padding-top:0">
  <div class="card" style="margin-top:8px">
    <h3>Marche en Direct</h3>
    <table>
      <thead><tr>
        <th>Paire</th><th>Prix</th><th>1m %</th><th>High</th><th>Low</th>
        <th>Volume</th><th>Signal</th><th>Score</th><th>Conf.</th>
      </tr></thead>
      <tbody id="mkt-tb"></tbody>
    </table>
  </div>
  <div class="card" style="margin-top:8px">
    <h3>Indicateurs par Paire</h3>
    <div id="ind-box"></div>
  </div>
</div>

<!-- ANALYSE APPROFONDIE + POSITIONS + TRADES -->
<div class="g3" style="padding-top:0">
  <div class="card" style="margin-top:8px">
    <h3>Analyse Approfondie</h3>
    <div id="deep-box"></div>
  </div>
  <div class="card" style="margin-top:8px">
    <h3>Positions Ouvertes</h3>
    <table>
      <thead><tr>
        <th>Paire</th><th>Type</th><th>Entree</th><th>Actuel</th>
        <th>PnL $</th><th>PnL %</th><th>SL</th><th>TP</th>
      </tr></thead>
      <tbody id="pos-tb"></tbody>
    </table>
  </div>
  <div class="card" style="margin-top:8px">
    <h3>Derniers Trades</h3>
    <table>
      <thead><tr>
        <th>Paire</th><th>T</th><th>In</th><th>Out</th>
        <th>PnL</th><th>%</th><th>H</th>
      </tr></thead>
      <tbody id="trd-tb"></tbody>
    </table>
  </div>
</div>

<!-- STATS + LOG -->
<div class="g2 pb" style="padding-top:0">
  <div class="card" style="margin-top:8px">
    <h3>Statistiques Avancees</h3>
    <table><tbody id="stats-tb"></tbody></table>
  </div>
  <div class="card" style="margin-top:8px">
    <h3>Journal d'Activite</h3>
    <div class="log" id="log-box"></div>
  </div>
</div>

<script>
// ── Charts ────────────────────────────────────────────────────────────────
let PC, AC;
const PH = { l: [], d: [] };

function initCharts() {
  const ctx1 = document.getElementById('pnlC').getContext('2d');
  PC = new Chart(ctx1, {
    type: 'line',
    data: { labels: PH.l, datasets: [{
      data: PH.d, borderColor: '#00e87a',
      backgroundColor: 'rgba(0,232,122,0.05)',
      borderWidth: 1.5, pointRadius: 0, fill: true, tension: 0.3
    }]},
    options: {
      responsive: true, animation: false,
      plugins: { legend: { display: false },
        tooltip: { callbacks: { label: v => (v.raw >= 0 ? '+' : '') + v.raw.toFixed(2) + ' USDT' } } },
      scales: {
        x: { display: false },
        y: { grid: { color: '#162030' }, ticks: { color: '#4a5c70',
          callback: v => (v >= 0 ? '+' : '') + v.toFixed(1) + '$' } }
      }
    }
  });
  const ctx2 = document.getElementById('allocC').getContext('2d');
  AC = new Chart(ctx2, {
    type: 'doughnut',
    data: { labels: ['Cash'], datasets: [{ data: [100],
      backgroundColor: ['#00d4ff','#00e87a','#f5a623','#ff4455','#aa44ff','#ff88aa'],
      borderWidth: 0 }] },
    options: { responsive: true, animation: false,
      plugins: { legend: { position: 'bottom',
        labels: { color: '#4a5c70', font: { size: 10 }, boxWidth: 8, padding: 8 } } } }
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────
const f   = (v, d = 2) => (v >= 0 ? '+' : '') + Number(v).toFixed(d);
const cc  = v => v >= 0 ? 'g' : 'r';
const clr = v => v >= 0 ? '#00e87a' : '#ff4455';
function minibar(ratio, color) {
  const w = Math.min(100, Math.max(0, Math.round(ratio * 100)));
  return `<div class="bw"><div class="bf" style="width:${w}%;background:${color}"></div></div>`;
}
function scorebar(label, val, max) {
  const ratio = Math.min(1, Math.abs(val) / (max || 1));
  const color = clr(val);
  return `<div class="sb">
    <span class="sb-lbl">${label}</span>
    <span class="sb-val" style="color:${color}">${f(val, 1)}</span>
    <div class="sb-bar"><div class="bw"><div class="bf" style="width:${Math.round(ratio*100)}%;background:${color}"></div></div></div>
  </div>`;
}

// ── Main update loop ──────────────────────────────────────────────────────
function update() {
  fetch('/api/data')
    .then(r => r.json())
    .then(d => {
      if (!d.ok) return;
      document.getElementById('clock').textContent = new Date().toLocaleTimeString('fr-FR');

      // Ticker
      document.getElementById('ticker').innerHTML =
        Object.entries(d.market).map(([p, i]) => {
          const col = clr(i.change_1m);
          const arr = i.change_1m >= 0 ? '&#9650;' : '&#9660;';
          return `<span><b style="color:#7a9abf">${p}</b>&nbsp;
            <span style="color:${col}">${arr}&nbsp;${i.price.toFixed(2)}&nbsp;
            <small>(${f(i.change_1m, 2)}%)</small></span></span>`;
        }).join('') || '<span class="dim">Chargement...</span>';

      // KPIs
      const p = d.portfolio;
      document.getElementById('k-tot').textContent = p.total.toFixed(2) + ' USDT';
      document.getElementById('k-tot').className   = 'big ' + cc(p.pnl);
      document.getElementById('k-roi').textContent = `ROI: ${f(p.roi, 2)}%  |  Init: ${p.initial.toFixed(0)} USDT`;
      document.getElementById('k-pnl').textContent = f(p.pnl, 2) + ' USDT';
      document.getElementById('k-pnl').className   = 'big ' + cc(p.pnl);
      document.getElementById('k-trades').textContent = `${p.total_trades} trades  |  ${p.cycles} cycles`;
      const wr = p.win_rate;
      document.getElementById('k-wr').textContent = wr.toFixed(1) + '%';
      document.getElementById('k-wr').className   = 'big ' + (wr >= 50 ? 'g' : 'r');
      document.getElementById('k-wrb').style.width = wr + '%';
      document.getElementById('k-wrb').style.background = clr(wr - 50);
      document.getElementById('k-wrs').textContent = `${p.wins} W  /  ${p.losses} L`;
      document.getElementById('k-pos').textContent = Object.keys(p.positions).length + ' position(s)';
      document.getElementById('k-cash').textContent =
        `Cash: ${p.cash.toFixed(2)} USDT  |  En jeu: ${p.in_pos.toFixed(2)} USDT`;

      // PnL Chart
      PH.l.push(new Date().toLocaleTimeString('fr-FR'));
      PH.d.push(p.pnl);
      if (PH.l.length > 200) { PH.l.shift(); PH.d.shift(); }
      const pColor = clr(p.pnl);
      PC.data.datasets[0].borderColor      = pColor;
      PC.data.datasets[0].backgroundColor  = p.pnl >= 0 ? 'rgba(0,232,122,0.05)' : 'rgba(255,68,85,0.05)';
      PC.update('none');

      // Alloc Chart
      const al = ['Cash'], av = [p.cash];
      Object.entries(p.positions).forEach(([s, pos]) => { al.push(s); av.push(pos.current_value); });
      AC.data.labels = al;
      AC.data.datasets[0].data = av;
      AC.update('none');

      // Marche table
      document.getElementById('mkt-tb').innerHTML =
        Object.entries(d.market).map(([pair, i]) => {
          const c   = cc(i.change_1m);
          const arr = i.change_1m >= 0 ? '&#9650;' : '&#9660;';
          const sigCls = i.signal === 'BUY' ? 'tl' : i.signal === 'SELL' ? 'ts' : 'th';
          const sigLbl = i.signal === 'BUY' ? '&#9650; LONG' : i.signal === 'SELL' ? '&#9660; SHORT' : '&#8213; HOLD';
          const sc  = (i.score || 0);
          const str = Math.min(1, Math.max(0, i.strength || 0));
          return `<tr>
            <td><b class="w">${pair}</b></td>
            <td class="${c}">${i.price.toFixed(2)}</td>
            <td class="${c}">${f(i.change_1m, 3)}%</td>
            <td class="dim">${i.high.toFixed(2)}</td>
            <td class="dim">${i.low.toFixed(2)}</td>
            <td class="dim">${i.volume.toFixed(0)}</td>
            <td><span class="tag ${sigCls}">${sigLbl}</span></td>
            <td class="${cc(sc)}">${f(sc, 1)}</td>
            <td style="min-width:60px">${minibar(str, clr(sc))}</td>
          </tr>`;
        }).join('') || '<tr><td colspan="9" class="dim" style="text-align:center">Chargement...</td></tr>';

      // Indicateurs
      document.getElementById('ind-box').innerHTML =
        Object.entries(d.indicators).map(([pair, ind]) => {
          const rc = ind.rsi > 70 ? 'r' : ind.rsi < 30 ? 'g' : 'y';
          const mc = ind.macd >= 0 ? 'g' : 'r';
          const bc = ind.bb_pct > 0.8 ? 'r' : ind.bb_pct < 0.2 ? 'g' : 'w';
          const ac = ind.adx > 30 ? 'g' : 'y';
          return `<div style="margin-bottom:9px;padding-bottom:7px;border-bottom:1px solid #0a1520">
            <span class="b" style="font-size:.76em;font-weight:600">${pair}</span>
            <div class="ig">
              <span class="il">RSI14 <b class="${rc}">${Number(ind.rsi).toFixed(1)}</b></span>
              <span class="il">MACD  <b class="${mc}">${Number(ind.macd).toFixed(2)}</b></span>
              <span class="il">ADX   <b class="${ac}">${Number(ind.adx).toFixed(1)}</b></span>
              <span class="il">BB%   <b class="${bc}">${(ind.bb_pct * 100).toFixed(0)}%</b></span>
            </div>
          </div>`;
        }).join('') || '<span class="dim" style="font-size:.8em">Chargement...</span>';

      // Analyse approfondie
      document.getElementById('deep-box').innerHTML =
        Object.entries(d.analysis).map(([pair, a]) => {
          const sc   = a.total_score || 0;
          const scCls = sc >= 4 ? 'tl' : sc <= -4 ? 'ts' : 'th';
          const tags  = (a.signals || []).slice(0, 5)
            .map(s => `<span class="tag th" style="margin:1px 2px;font-size:.65em">${s}</span>`).join('');
          const pats  = (a.patterns || [])
            .map(s => `<span class="tag tl" style="margin:1px 2px;font-size:.65em">${s}</span>`).join('');
          return `<div style="margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #0a1520">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:5px">
              <b class="b" style="font-size:.82em">${pair}</b>
              <span class="tag ${scCls}">${f(sc, 1)} pts</span>
            </div>
            ${scorebar('Tendance',  a.trend_score,    10)}
            ${scorebar('Momentum', a.momentum_score, 10)}
            ${scorebar('Volume',   a.volume_score,    6)}
            ${scorebar('Patterns', a.pattern_score,   6)}
            ${scorebar('Multi-TF', a.mtf_score,       6)}
            <div style="margin-top:5px;line-height:1.8">${tags}${pats}</div>
          </div>`;
        }).join('') || '<span class="dim" style="font-size:.8em">Chargement...</span>';

      // Positions
      document.getElementById('pos-tb').innerHTML =
        Object.entries(p.positions).map(([sym, pos]) => {
          const c   = cc(pos.pnl);
          const tcl = pos.type === 'short' ? 'ts' : 'tl';
          return `<tr>
            <td><b class="w">${sym}</b></td>
            <td><span class="tag ${tcl}">${pos.type.toUpperCase()}</span></td>
            <td>${pos.entry.toFixed(2)}</td>
            <td class="${c}">${pos.current.toFixed(2)}</td>
            <td class="${c}">${f(pos.pnl)}</td>
            <td class="${c}">${f(pos.pnl_pct)}%</td>
            <td class="r">${pos.sl.toFixed(2)}</td>
            <td class="g">${pos.tp.toFixed(2)}</td>
          </tr>`;
        }).join('') || '<tr><td colspan="8" class="dim" style="text-align:center;padding:10px">Aucune position ouverte</td></tr>';

      // Trades
      document.getElementById('trd-tb').innerHTML =
        [...d.trades].reverse().slice(0, 10).map(t => {
          const c   = cc(t.pnl);
          const tcl = t.type === 'short' ? 'ts' : 'tl';
          return `<tr>
            <td><b class="w">${t.symbol}</b></td>
            <td><span class="tag ${tcl}">${t.type[0].toUpperCase()}</span></td>
            <td>${t.entry.toFixed(2)}</td>
            <td>${t.exit.toFixed(2)}</td>
            <td class="${c}">${f(t.pnl)}</td>
            <td class="${c}">${f(t.pnl_pct)}%</td>
            <td class="dim">${t.time}</td>
          </tr>`;
        }).join('') || '<tr><td colspan="7" class="dim" style="text-align:center;padding:10px">Aucun trade</td></tr>';

      // Stats
      const s = d.stats;
      document.getElementById('stats-tb').innerHTML = [
        ['Profit moyen / trade', f(s.avg_pnl) + ' USDT',  cc(s.avg_pnl)],
        ['Meilleur trade',  '<span class="g">' + f(s.best)  + ' USDT</span>', 'g'],
        ['Pire trade',      '<span class="r">' + f(s.worst) + ' USDT</span>', 'r'],
        ['Profit Factor',   Number(s.pf).toFixed(2),     s.pf >= 1 ? 'g' : 'r'],
        ['Sharpe Ratio',    Number(s.sharpe).toFixed(2), s.sharpe >= 1 ? 'g' : 'y'],
        ['Capital en jeu',  s.invested.toFixed(2) + ' USDT', 'w'],
        ['Nb positions',    Object.keys(p.positions).length, 'y'],
        ['MAJ marche',      d.last_update || '--', 'b'],
      ].map(([k, v, c]) =>
        `<tr><td class="dim">${k}</td><td style="text-align:right" class="${c}">${v}</td></tr>`
      ).join('');

      // Log
      document.getElementById('log-box').innerHTML =
        [...(d.log || [])].reverse().slice(0, 25)
          .map(l => `<div class="ll">${l}</div>`).join('') ||
        '<div class="ll dim">Aucune activite</div>';
    })
    .catch(() => {});
}

document.addEventListener('DOMContentLoaded', () => { initCharts(); update(); setInterval(update, 1000); });
</script>
</body></html>
'''

# ─── Flask routes ────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return render_template_string(HTML)

@app.route('/api/data')
def api_data():
    if not _portfolio:
        return jsonify({'ok': False})
    p = _portfolio
    market     = _cache.get('market', {})
    indicators = _cache.get('indicators', {})
    analysis   = _cache.get('analysis', {})

    # Calcul positions
    pos_val = 0
    positions_out = {}
    for sym, pos in p.positions.items():
        curr = market.get(sym, {}).get('price', pos['entry_price'])
        t = pos.get('trade_type', 'long')
        if t == 'short':
            pnl     = (pos['entry_price'] - curr) * pos['amount']
            pnl_pct = (pos['entry_price'] - curr) / pos['entry_price'] * 100
            sl = pos['entry_price'] * 1.10
            tp = pos['entry_price'] * 0.80
        else:
            pnl     = (curr - pos['entry_price']) * pos['amount']
            pnl_pct = (curr - pos['entry_price']) / pos['entry_price'] * 100
            sl = pos['entry_price'] * 0.90
            tp = pos['entry_price'] * 1.20
        val = curr * pos['amount']
        pos_val += val
        positions_out[sym] = {
            'entry': pos['entry_price'], 'current': curr,
            'amount': pos['amount'],     'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2), 'current_value': round(val, 2),
            'sl': round(sl, 2), 'tp': round(tp, 2), 'type': t
        }

    total   = p.cash + pos_val
    pnl_t   = total - p.initial_capital
    roi     = pnl_t / p.initial_capital * 100
    wins    = sum(1 for t in p.trade_history if t['pnl'] > 0)
    losses  = len(p.trade_history) - wins
    wr      = wins / len(p.trade_history) * 100 if p.trade_history else 0
    pnls    = [t['pnl'] for t in p.trade_history]
    gains   = sum(x for x in pnls if x > 0)
    loss_s  = abs(sum(x for x in pnls if x < 0))
    pf      = round(gains / loss_s, 3) if loss_s > 0 else 0.0
    sharpe  = 0.0
    if len(pnls) > 2:
        try: sharpe = round(statistics.mean(pnls) / statistics.stdev(pnls), 3)
        except: pass

    trades_out = [{
        'symbol': t['symbol'], 'entry': t['entry_price'], 'exit': t['exit_price'],
        'pnl': round(t['pnl'], 2), 'pnl_pct': round(t.get('pnl_pct', 0), 2),
        'time': t['exit_time'].strftime('%H:%M:%S') if 'exit_time' in t else '--',
        'type': t.get('trade_type', 'long')
    } for t in p.trade_history]

    return jsonify({
        'ok': True,
        'portfolio': {
            'total': round(total, 2),    'cash': round(p.cash, 2),
            'pnl':  round(pnl_t, 2),    'roi':  round(roi, 2),
            'initial': p.initial_capital, 'in_pos': round(pos_val, 2),
            'total_trades': len(p.trade_history), 'cycles': getattr(p, 'cycles', 0),
            'wins': wins, 'losses': losses, 'win_rate': round(wr, 1),
            'positions': positions_out
        },
        'market':     market,
        'indicators': indicators,
        'analysis':   analysis,
        'trades':     trades_out,
        'stats': {
            'avg_pnl':  round(sum(pnls) / len(pnls), 2) if pnls else 0,
            'best':     round(max(pnls), 2) if pnls else 0,
            'worst':    round(min(pnls), 2) if pnls else 0,
            'pf': pf, 'sharpe': sharpe,
            'invested': round(pos_val, 2)
        },
        'log':         getattr(p, 'activity_log', []),
        'last_update': _cache.get('last_update', '--')
    })

def run_dashboard(portfolio, exchange):
    global _portfolio, _exchange
    _portfolio = portfolio
    _exchange  = exchange
    threading.Thread(target=_update_cache, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
