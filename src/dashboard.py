from flask import Flask, render_template_string, jsonify
from datetime import datetime
import threading
import time

app = Flask(__name__)

_portfolio = None
_exchange = None

# Cache mis a jour par un thread dedie (pas a chaque requete)
_cache = {
    'market': {},
    'indicators': {},
    'last_update': None
}

def _update_cache():
    """Thread dedie qui met a jour le cache marche toutes les 2s"""
    while True:
        try:
            if _exchange is None:
                time.sleep(2)
                continue
            pairs = ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT']
            from src.strategy import TradingStrategy
            strat = TradingStrategy()
            for pair in pairs:
                try:
                    ohlcv = _exchange.get_ohlcv(pair, timeframe='1m', limit=100)
                    if ohlcv is None or len(ohlcv) < 20:
                        continue
                    df = ohlcv.copy()
                    # Indicateurs manuels sans dependre de compute_indicators
                    close = df['close']
                    # RSI
                    delta = close.diff()
                    gain = delta.clip(lower=0).rolling(14).mean()
                    loss = (-delta.clip(upper=0)).rolling(14).mean()
                    rs = gain / loss.replace(0, 0.0001)
                    rsi = float((100 - 100 / (1 + rs)).iloc[-1])
                    # MACD
                    ema12 = close.ewm(span=12).mean()
                    ema26 = close.ewm(span=26).mean()
                    macd_line = ema12 - ema26
                    signal_line = macd_line.ewm(span=9).mean()
                    macd_hist = float((macd_line - signal_line).iloc[-1])
                    # Bollinger
                    sma20 = close.rolling(20).mean()
                    std20 = close.rolling(20).std()
                    bb_upper = sma20 + 2 * std20
                    bb_lower = sma20 - 2 * std20
                    bb_pct = float(((close - bb_lower) / (bb_upper - bb_lower + 0.0001)).iloc[-1])
                    # ADX simplifie
                    adx = 25.0  # valeur fixe si pas de lib ADX
                    try:
                        import ta
                        adx = float(ta.trend.ADXIndicator(df['high'], df['low'], df['close'], window=14).adx().iloc[-1])
                    except:
                        pass
                    last = df.iloc[-1]
                    prev = df.iloc[-2]
                    change_1m = float((last['close'] - prev['close']) / prev['close'] * 100)
                    # Signal
                    try:
                        sig = strat.generate_signal(ohlcv, pair)
                        action = sig['action']
                        confidence = float(sig['confidence'])
                    except:
                        action = 'HOLD'
                        confidence = 0.0
                    _cache['market'][pair] = {
                        'price': float(last['close']),
                        'open': float(last['open']),
                        'high': float(last['high']),
                        'low': float(last['low']),
                        'volume': float(last['volume']),
                        'change_1m': change_1m,
                        'signal': action,
                        'strength': confidence
                    }
                    _cache['indicators'][pair] = {
                        'rsi': rsi, 'macd': macd_hist,
                        'adx': adx, 'bb_pct': bb_pct
                    }
                except Exception as e:
                    pass
            _cache['last_update'] = datetime.now().strftime('%H:%M:%S')
        except Exception as e:
            pass
        time.sleep(2)

HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>AI Crypto Bot</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0e1a;color:#e0e0e0;font-family:"Segoe UI",monospace;font-size:14px}
.header{background:linear-gradient(90deg,#0d1b2a,#1a2f4e);padding:14px 20px;border-bottom:2px solid #00d4ff;display:flex;justify-content:space-between;align-items:center}
.header h1{color:#00d4ff;font-size:1.2em;letter-spacing:2px}
.badge{padding:3px 10px;border-radius:12px;font-size:.72em;font-weight:bold}
.ticker{display:flex;gap:20px;padding:8px 20px;background:#0d1520;border-bottom:1px solid #1f2d40;font-size:.82em;flex-wrap:wrap}
.grid4{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;padding:12px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:0 12px 12px}
.grid21{display:grid;grid-template-columns:2fr 1fr;gap:10px;padding:0 12px 12px}
.card{background:#111827;border:1px solid #1f2d40;border-radius:8px;padding:14px}
.card h3{color:#00d4ff;font-size:.75em;letter-spacing:1px;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid #1f2d40;text-transform:uppercase}
.big{font-size:2em;font-weight:bold;margin:4px 0}
.sub{font-size:.75em;color:#888;margin-top:2px}
.green{color:#00ff88}.red{color:#ff4444}.yellow{color:#f5a623}.blue{color:#00d4ff}.white{color:#fff}
table{width:100%;border-collapse:collapse;font-size:.8em}
th{color:#00d4ff;text-align:left;padding:5px 8px;border-bottom:1px solid #1f2d40;font-weight:500;letter-spacing:.5px}
td{padding:5px 8px;border-bottom:1px solid #0d1520}
tr:hover{background:#0d1b2a55}
.tag{display:inline-block;padding:1px 7px;border-radius:8px;font-size:.72em;font-weight:bold}
.long{background:#00ff8820;color:#00ff88;border:1px solid #00ff8866}
.short{background:#ff444420;color:#ff4444;border:1px solid #ff444466}
.hold{background:#f5a62320;color:#f5a623;border:1px solid #f5a62366}
.bar-wrap{background:#1f2d40;border-radius:3px;height:5px;margin-top:4px}
.bar{height:5px;border-radius:3px}
.log-box{height:160px;overflow-y:auto;font-size:.76em}
.log-line{padding:2px 0;border-bottom:1px solid #0d1520;color:#aaa}
.ind-card{margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #1f2d40}
.ind-grid{display:grid;grid-template-columns:1fr 1fr;gap:4px;font-size:.75em;margin-top:4px}
.status-dot{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:6px}
</style>
</head>
<body>
<div class="header">
  <h1>&#9889; AI CRYPTO TRADING BOT</h1>
  <div style="display:flex;gap:10px;align-items:center">
    <span id="clock" style="color:#888;font-size:.85em"></span>
    <span class="badge" style="background:#f5a62333;color:#f5a623;border:1px solid #f5a623">PAPER MODE</span>
    <span class="badge" style="background:#00ff8833;color:#00ff88;border:1px solid #00ff88">
      <span class="status-dot" style="background:#00ff88"></span>LIVE
    </span>
  </div>
</div>

<div class="ticker" id="ticker"><span style="color:#888">Chargement des prix...</span></div>

<div class="grid4">
  <div class="card">
    <h3>Capital Total</h3>
    <div class="big blue" id="s-total">--</div>
    <div class="sub" id="s-roi">ROI: --</div>
  </div>
  <div class="card">
    <h3>PnL Unrealise</h3>
    <div class="big" id="s-pnl">--</div>
    <div class="sub" id="s-trades">0 trades fermes</div>
  </div>
  <div class="card">
    <h3>Win Rate</h3>
    <div class="big" id="s-wr">--%</div>
    <div class="bar-wrap"><div class="bar green" id="s-wr-bar" style="width:0%"></div></div>
    <div class="sub" id="s-wrsub">0 W / 0 L</div>
  </div>
  <div class="card">
    <h3>Positions / Cash</h3>
    <div class="big yellow" id="s-pos">0</div>
    <div class="sub" id="s-cash">Cash: -- USDT</div>
  </div>
</div>

<div class="grid2">
  <div class="card">
    <h3>Courbe PnL en temps reel</h3>
    <canvas id="pnlChart" height="80"></canvas>
  </div>
  <div class="card">
    <h3>Repartition du Capital</h3>
    <canvas id="allocChart" height="80"></canvas>
  </div>
</div>

<div class="grid21">
  <div class="card">
    <h3>Marche en Direct</h3>
    <table>
      <thead><tr><th>Paire</th><th>Prix</th><th>Variation 1m</th><th>High</th><th>Low</th><th>Volume</th><th>Signal</th><th>Force</th></tr></thead>
      <tbody id="market-tb"></tbody>
    </table>
  </div>
  <div class="card">
    <h3>Indicateurs Techniques</h3>
    <div id="indicators"><span style="color:#888">Chargement...</span></div>
  </div>
</div>

<div class="grid2">
  <div class="card">
    <h3>Positions Ouvertes</h3>
    <table>
      <thead><tr><th>Paire</th><th>Type</th><th>Entree</th><th>Actuel</th><th>PnL $</th><th>PnL %</th><th>SL</th><th>TP</th></tr></thead>
      <tbody id="pos-tb"></tbody>
    </table>
  </div>
  <div class="card">
    <h3>Historique Trades</h3>
    <table>
      <thead><tr><th>Paire</th><th>Type</th><th>Entree</th><th>Sortie</th><th>PnL $</th><th>PnL %</th><th>Heure</th></tr></thead>
      <tbody id="trade-tb"></tbody>
    </table>
  </div>
</div>

<div class="grid2" style="padding-bottom:20px">
  <div class="card">
    <h3>Statistiques Avancees</h3>
    <table><tbody id="stats-tb"></tbody></table>
  </div>
  <div class="card">
    <h3>Journal d\'Activite</h3>
    <div class="log-box" id="log-box"></div>
  </div>
</div>

<script>
let pnlChart, allocChart;
const pnlHistory = {labels:[], data:[]};

function initCharts() {
  const c1 = document.getElementById("pnlChart").getContext("2d");
  pnlChart = new Chart(c1, {
    type:"line",
    data:{labels:pnlHistory.labels, datasets:[{
      data:pnlHistory.data, borderColor:"#00d4ff",
      backgroundColor:"rgba(0,212,255,0.06)", borderWidth:2,
      pointRadius:0, fill:true, tension:0.3
    }]},
    options:{responsive:true, animation:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:v=>(v.raw>=0?"+":"")+v.raw.toFixed(2)+" USDT"}}},
      scales:{x:{display:false},y:{grid:{color:"#1f2d4066"},ticks:{color:"#888",callback:v=>(v>=0?"+":"")+v.toFixed(1)+"$"}}}}
  });
  const c2 = document.getElementById("allocChart").getContext("2d");
  allocChart = new Chart(c2, {
    type:"doughnut",
    data:{labels:["Cash"],datasets:[{data:[100],
      backgroundColor:["#00d4ff","#00ff88","#f5a623","#ff4444","#aa44ff","#ff88aa"],
      borderWidth:0}]},
    options:{responsive:true,animation:false,
      plugins:{legend:{position:"bottom",labels:{color:"#888",font:{size:10},boxWidth:10}}}}
  });
}

const f = (v,d=2) => (v>=0?"+":"")+v.toFixed(d);
const cc = v => v>=0?"green":"red";

function update() {
  fetch("/api/data").then(r=>r.json()).then(d => {
    if(!d.ok) return;
    document.getElementById("clock").textContent = new Date().toLocaleTimeString("fr-FR");

    // Ticker
    const mk = d.market;
    document.getElementById("ticker").innerHTML = Object.entries(mk).map(([p,i])=>{
      const c=i.change_1m>=0?"#00ff88":"#ff4444";
      const a=i.change_1m>=0?"&#9650;":"&#9660;";
      return `<span><b style="color:#e0e0e0">${p}</b> <span style="color:${c}">${a} ${i.price.toFixed(2)} <small>(${f(i.change_1m,2)}%)</small></span></span>`;
    }).join("") || "Chargement...";

    // Stats portfolio
    const p=d.portfolio;
    document.getElementById("s-total").textContent=p.total.toFixed(2)+" USDT";
    document.getElementById("s-total").className="big "+cc(p.pnl);
    document.getElementById("s-roi").textContent=`ROI: ${f(p.roi)}% | Initial: ${p.initial.toFixed(0)} USDT`;
    document.getElementById("s-pnl").textContent=f(p.pnl)+" USDT";
    document.getElementById("s-pnl").className="big "+cc(p.pnl);
    document.getElementById("s-trades").textContent=`${p.total_trades} trades | ${p.cycles} cycles`;
    const wr=p.win_rate;
    document.getElementById("s-wr").textContent=wr.toFixed(1)+"%";
    document.getElementById("s-wr").className="big "+(wr>=50?"green":"red");
    document.getElementById("s-wr-bar").style.width=wr+"%";
    document.getElementById("s-wr-bar").className="bar "+(wr>=50?"green":"red");
    document.getElementById("s-wrsub").textContent=`${p.wins} W / ${p.losses} L`;
    document.getElementById("s-pos").textContent=Object.keys(p.positions).length+" positions";
    document.getElementById("s-cash").textContent=`Cash: ${p.cash.toFixed(2)} USDT | En jeu: ${p.in_pos.toFixed(2)} USDT`;

    // PnL Chart
    pnlHistory.labels.push(new Date().toLocaleTimeString("fr-FR"));
    pnlHistory.data.push(p.pnl);
    if(pnlHistory.labels.length>180){pnlHistory.labels.shift();pnlHistory.data.shift();}
    // Couleur dynamique selon positif ou negatif
    pnlChart.data.datasets[0].borderColor = p.pnl>=0?"#00ff88":"#ff4444";
    pnlChart.data.datasets[0].backgroundColor = p.pnl>=0?"rgba(0,255,136,0.06)":"rgba(255,68,68,0.06)";
    pnlChart.update("none");

    // Alloc Chart
    const aLabels=["Cash"],aData=[p.cash];
    Object.entries(p.positions).forEach(([s,pos])=>{aLabels.push(s);aData.push(pos.current_value);});
    allocChart.data.labels=aLabels;
    allocChart.data.datasets[0].data=aData;
    allocChart.update("none");

    // Marche
    document.getElementById("market-tb").innerHTML=Object.entries(mk).map(([pair,i])=>{
      const c=i.change_1m>=0?"green":"red";
      const a=i.change_1m>=0?"&#9650;":"&#9660;";
      const sigCls=i.signal==="BUY"?"long":i.signal==="SELL"?"short":"hold";
      const sigLbl=i.signal==="BUY"?"LONG":i.signal==="SELL"?"SHORT":"HOLD";
      const str=Math.min(100,(i.strength*100)).toFixed(0);
      return `<tr>
        <td><b>${a} ${pair}</b></td>
        <td class="${c}">${i.price.toFixed(2)}</td>
        <td class="${c}">${f(i.change_1m,3)}%</td>
        <td>${i.high.toFixed(2)}</td>
        <td>${i.low.toFixed(2)}</td>
        <td>${i.volume.toFixed(0)}</td>
        <td><span class="tag ${sigCls}">${sigLbl}</span></td>
        <td><div class="bar-wrap"><div class="bar ${c}" style="width:${str}%"></div></div></td>
      </tr>`;
    }).join("") || '<tr><td colspan="8" style="color:#888">Chargement...</td></tr>';

    // Indicateurs
    document.getElementById("indicators").innerHTML=Object.entries(d.indicators).map(([pair,ind])=>{
      const rc=ind.rsi>70?"red":ind.rsi<30?"green":"yellow";
      const mc=ind.macd>=0?"green":"red";
      const bc=ind.bb_pct>0.8?"red":ind.bb_pct<0.2?"green":"white";
      return `<div class="ind-card">
        <span style="color:#00d4ff;font-size:.78em;font-weight:bold">${pair}</span>
        <div class="ind-grid">
          <span>RSI <b class="${rc}">${ind.rsi.toFixed(1)}</b></span>
          <span>MACD <b class="${mc}">${ind.macd.toFixed(3)}</b></span>
          <span>ADX <b class="${ind.adx>25?"green":"yellow"}">${ind.adx.toFixed(1)}</b></span>
          <span>BB% <b class="${bc}">${(ind.bb_pct*100).toFixed(0)}%</b></span>
        </div>
      </div>`;
    }).join("") || '<span style="color:#888">Chargement...</span>';

    // Positions
    document.getElementById("pos-tb").innerHTML=Object.entries(p.positions).map(([sym,pos])=>{
      const c=cc(pos.pnl);
      const tCls=pos.type==="short"?"short":"long";
      return `<tr>
        <td><b>${sym}</b></td>
        <td><span class="tag ${tCls}">${pos.type.toUpperCase()}</span></td>
        <td>${pos.entry.toFixed(2)}</td>
        <td class="${c}">${pos.current.toFixed(2)}</td>
        <td class="${c}">${f(pos.pnl)}</td>
        <td class="${c}">${f(pos.pnl_pct)}%</td>
        <td class="red">${pos.sl.toFixed(2)}</td>
        <td class="green">${pos.tp.toFixed(2)}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="8" class="" style="color:#888;text-align:center;padding:12px">Aucune position ouverte</td></tr>';

    // Trades
    document.getElementById("trade-tb").innerHTML=[...d.trades].reverse().slice(0,8).map(t=>{
      const c=cc(t.pnl);
      const tCls=t.type==="short"?"short":"long";
      return `<tr>
        <td><b>${t.symbol}</b></td>
        <td><span class="tag ${tCls}">${t.type.toUpperCase()}</span></td>
        <td>${t.entry.toFixed(2)}</td>
        <td>${t.exit.toFixed(2)}</td>
        <td class="${c}">${f(t.pnl)}</td>
        <td class="${c}">${f(t.pnl_pct)}%</td>
        <td style="color:#666">${t.time}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="7" style="color:#888;text-align:center;padding:12px">Aucun trade ferme</td></tr>';

    // Stats avancees
    const s=d.stats;
    document.getElementById("stats-tb").innerHTML=[
      ["Profit moyen / trade", f(s.avg_pnl)+" USDT"],
      ["Meilleur trade", "<span class=\'green\'>"+f(s.best)+" USDT</span>"],
      ["Pire trade", "<span class=\'red\'>"+f(s.worst)+" USDT</span>"],
      ["Profit Factor", s.pf.toFixed(2)],
      ["Sharpe Ratio", s.sharpe.toFixed(2)],
      ["Total investi en cours", s.invested.toFixed(2)+" USDT"],
      ["Nb positions ouvertes", Object.keys(p.positions).length],
      ["Derniere MAJ marche", d.last_update || "--"],
    ].map(([k,v])=>`<tr><td style="color:#888">${k}</td><td style="text-align:right">${v}</td></tr>`).join("");

    // Log
    document.getElementById("log-box").innerHTML=
      [...(d.log||[])].reverse().slice(0,20)
      .map(l=>`<div class="log-line">${l}</div>`).join("") || '<div class="log-line" style="color:#666">Aucune activite</div>';

  }).catch(e => console.warn("API error:", e));
}

document.addEventListener("DOMContentLoaded",()=>{
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
        return jsonify({'ok': False})
    p = _portfolio
    market = _cache.get('market', {})
    indicators = _cache.get('indicators', {})

    pos_val = 0
    positions_out = {}
    for sym, pos in p.positions.items():
        curr = market.get(sym, {}).get('price', pos['entry_price'])
        trade_type = pos.get('trade_type', 'long')
        if trade_type == 'short':
            pnl = (pos['entry_price'] - curr) * pos['amount']
            pnl_pct = (pos['entry_price'] - curr) / pos['entry_price'] * 100
            sl = pos['entry_price'] * 1.10
            tp = pos['entry_price'] * 0.80
        else:
            pnl = (curr - pos['entry_price']) * pos['amount']
            pnl_pct = (curr - pos['entry_price']) / pos['entry_price'] * 100
            sl = pos['entry_price'] * 0.90
            tp = pos['entry_price'] * 1.20
        val = curr * pos['amount']
        pos_val += val
        positions_out[sym] = {
            'entry': pos['entry_price'], 'current': curr,
            'amount': pos['amount'], 'pnl': round(pnl, 2),
            'pnl_pct': round(pnl_pct, 2), 'current_value': round(val, 2),
            'sl': round(sl, 2), 'tp': round(tp, 2),
            'type': trade_type
        }

    total = p.cash + pos_val
    pnl_total = total - p.initial_capital
    roi = pnl_total / p.initial_capital * 100
    wins = sum(1 for t in p.trade_history if t['pnl'] > 0)
    losses = len(p.trade_history) - wins
    win_rate = wins / len(p.trade_history) * 100 if p.trade_history else 0

    pnls = [t['pnl'] for t in p.trade_history]
    gains = sum(x for x in pnls if x > 0)
    loss_sum = abs(sum(x for x in pnls if x < 0))
    pf = gains / loss_sum if loss_sum > 0 else 0.0
    try:
        import statistics
        sharpe = statistics.mean(pnls) / statistics.stdev(pnls) if len(pnls) > 2 else 0.0
    except:
        sharpe = 0.0

    trades_out = [{
        'symbol': t['symbol'], 'entry': t['entry_price'], 'exit': t['exit_price'],
        'pnl': round(t['pnl'], 2), 'pnl_pct': round(t.get('pnl_pct', 0), 2),
        'time': t['exit_time'].strftime('%H:%M:%S') if 'exit_time' in t else '--',
        'type': t.get('trade_type', 'long')
    } for t in p.trade_history]

    return jsonify({
        'ok': True,
        'portfolio': {
            'total': round(total, 2), 'cash': round(p.cash, 2),
            'pnl': round(pnl_total, 2), 'roi': round(roi, 2),
            'initial': p.initial_capital, 'in_pos': round(pos_val, 2),
            'total_trades': len(p.trade_history),
            'wins': wins, 'losses': losses, 'win_rate': round(win_rate, 1),
            'positions': positions_out, 'cycles': getattr(p, 'cycles', 0)
        },
        'market': market,
        'indicators': indicators,
        'trades': trades_out,
        'stats': {
            'avg_pnl': sum(pnls)/len(pnls) if pnls else 0,
            'best': max(pnls) if pnls else 0,
            'worst': min(pnls) if pnls else 0,
            'pf': pf, 'sharpe': sharpe,
            'invested': round(pos_val, 2)
        },
        'log': getattr(p, 'activity_log', []),
        'last_update': _cache.get('last_update', '--')
    })

def run_dashboard(portfolio, exchange):
    global _portfolio, _exchange
    _portfolio = portfolio
    _exchange = exchange
    threading.Thread(target=_update_cache, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
