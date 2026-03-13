from flask import Flask, render_template_string, jsonify
from datetime import datetime
import threading
import time

app = Flask(__name__)
_portfolio = None
_exchange  = None
_cache = {'market': {}, 'indicators': {}, 'analysis': {}, 'last_update': None}

def _update_cache():
    while True:
        try:
            if _exchange is None:
                time.sleep(2); continue
            pairs = ['BTC/USDT','ETH/USDT','SOL/USDT','BNB/USDT']
            from src.strategy import TradingStrategy
            strat = TradingStrategy()
            strat.set_exchange(_exchange)
            for pair in pairs:
                try:
                    ohlcv = _exchange.get_ohlcv(pair, timeframe='1m', limit=200)
                    if ohlcv is None or len(ohlcv) < 30: continue
                    sig = strat.generate_signal(ohlcv, pair)
                    last = ohlcv.iloc[-1]
                    prev = ohlcv.iloc[-2]
                    change = float((last['close'] - prev['close']) / prev['close'] * 100)
                    _cache['market'][pair] = {
                        'price': float(last['close']),
                        'high':  float(last['high']),
                        'low':   float(last['low']),
                        'volume':float(last['volume']),
                        'change_1m': change,
                        'signal':   sig['action'],
                        'strength': sig['confidence']
                    }
                    _cache['indicators'][pair] = {
                        'rsi':  sig['rsi'], 'adx': sig['adx'],
                        'bb_pct': sig['bb_pct'], 'macd': sig.get('momentum_score',0)
                    }
                    _cache['analysis'][pair] = sig
                except Exception as e:
                    pass
            _cache['last_update'] = datetime.now().strftime('%H:%M:%S')
        except: pass
        time.sleep(3)

HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<title>AI Crypto Bot Pro</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#060b14;color:#d0d8e8;font-family:"Segoe UI",sans-serif;font-size:13px}
a,a:visited{color:#00d4ff}
.header{background:linear-gradient(90deg,#060b14,#0d1f35);padding:12px 20px;border-bottom:2px solid #00d4ff33;display:flex;justify-content:space-between;align-items:center}
.header h1{color:#00d4ff;font-size:1.1em;letter-spacing:3px;font-weight:600}
.badge{padding:2px 9px;border-radius:10px;font-size:.7em;font-weight:bold}
.ticker-bar{display:flex;gap:18px;padding:7px 20px;background:#080f1a;border-bottom:1px solid #0d1f35;font-size:.8em;flex-wrap:wrap;overflow:hidden}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:10px}
.g2{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:0 10px 10px}
.g31{display:grid;grid-template-columns:3fr 1fr;gap:8px;padding:0 10px 10px}
.g211{display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;padding:0 10px 10px}
.card{background:#0d1520;border:1px solid #1a2a3a;border-radius:8px;padding:12px}
.card h3{color:#00d4ff;font-size:.72em;letter-spacing:1.5px;margin-bottom:8px;padding-bottom:5px;border-bottom:1px solid #1a2a3a;text-transform:uppercase}
.big{font-size:1.9em;font-weight:700;margin:2px 0}
.sub{font-size:.72em;color:#667;margin-top:3px}
.g{color:#00ff88}.r{color:#ff4444}.y{color:#f5a623}.b{color:#00d4ff}.w{color:#fff}
table{width:100%;border-collapse:collapse;font-size:.78em}
th{color:#00d4ff55;text-align:left;padding:4px 6px;border-bottom:1px solid #1a2a3a;font-weight:500;font-size:.75em;letter-spacing:.5px;text-transform:uppercase}
td{padding:4px 6px;border-bottom:1px solid #0a1420;vertical-align:middle}
tr:hover td{background:#0d1f3522}
.tag{display:inline-block;padding:1px 6px;border-radius:6px;font-size:.7em;font-weight:700}
.tl{background:#00ff8818;color:#00ff88;border:1px solid #00ff8844}
.ts{background:#ff444418;color:#ff4444;border:1px solid #ff444444}
.th{background:#f5a62318;color:#f5a623;border:1px solid #f5a62344}
.bar-bg{background:#1a2a3a;border-radius:3px;height:4px}
.bar-fill{height:4px;border-radius:3px;transition:width .4s}
.score-bar{display:flex;align-items:center;gap:6px;margin:3px 0;font-size:.75em}
.score-label{width:90px;color:#667;flex-shrink:0}
.score-val{width:38px;text-align:right;font-weight:600}
.log{height:150px;overflow-y:auto;font-size:.74em}
.logline{padding:2px 0;border-bottom:1px solid #0a1420;color:#556}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block;margin-right:5px;animation:blink 1.5s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
</style>
</head>
<body>
<div class="header">
  <h1>&#9889; AI CRYPTO TRADING BOT PRO</h1>
  <div style="display:flex;gap:8px;align-items:center">
    <span id="clock" style="color:#445;font-size:.82em"></span>
    <span class="badge" style="background:#f5a62322;color:#f5a623;border:1px solid #f5a62344">PAPER</span>
    <span class="badge" style="background:#00ff8822;color:#00ff88;border:1px solid #00ff8844">
      <span class="dot" style="background:#00ff88"></span>LIVE
    </span>
  </div>
</div>
<div class="ticker-bar" id="ticker">Chargement...</div>

<!-- KPIs -->
<div class="g4">
  <div class="card"><h3>Capital</h3><div class="big b" id="k-total">--</div><div class="sub" id="k-roi"></div></div>
  <div class="card"><h3>PnL Non Realise</h3><div class="big" id="k-pnl">--</div><div class="sub" id="k-trades"></div></div>
  <div class="card"><h3>Win Rate</h3><div class="big" id="k-wr">--</div>
    <div class="bar-bg" style="margin-top:5px"><div class="bar-fill" id="k-wr-bar" style="width:0%;background:#00ff88"></div></div>
    <div class="sub" id="k-wrsub"></div></div>
  <div class="card"><h3>Positions / Cash</h3><div class="big y" id="k-pos">--</div><div class="sub" id="k-cash"></div></div>
</div>

<!-- Charts -->
<div class="g2">
  <div class="card"><h3>Courbe PnL Temps Reel</h3><canvas id="pnlC" height="85"></canvas></div>
  <div class="card"><h3>Allocation Capital</h3><canvas id="allocC" height="85"></canvas></div>
</div>

<!-- Marche + Analyse -->
<div class="g31">
  <div class="card">
    <h3>Marche en Direct</h3>
    <table><thead><tr><th>Paire</th><th>Prix</th><th>1m%</th><th>High</th><th>Low</th><th>Vol</th><th>Signal</th><th>Score</th><th>Force</th></tr></thead>
    <tbody id="mkt-tb"></tbody></table>
  </div>
  <div class="card">
    <h3>Analyse Technique</h3>
    <div id="ind-box"></div>
  </div>
</div>

<!-- Analyse approfondie -->
<div class="g211">
  <div class="card">
    <h3>Analyse Approfondie par Paire</h3>
    <div id="deep-box"></div>
  </div>
  <div class="card">
    <h3>Positions Ouvertes</h3>
    <table><thead><tr><th>Paire</th><th>Type</th><th>Entree</th><th>Actuel</th><th>PnL</th><th>%</th><th>SL</th><th>TP</th></tr></thead>
    <tbody id="pos-tb"></tbody></table>
  </div>
  <div class="card">
    <h3>Derniers Trades</h3>
    <table><thead><tr><th>Paire</th><th>T</th><th>In</th><th>Out</th><th>PnL</th><th>%</th><th>H</th></tr></thead>
    <tbody id="trd-tb"></tbody></table>
  </div>
</div>

<!-- Stats + Log -->
<div class="g2" style="padding-bottom:16px">
  <div class="card">
    <h3>Statistiques Avancees</h3>
    <table><tbody id="stats-tb"></tbody></table>
  </div>
  <div class="card">
    <h3>Journal Activite</h3>
    <div class="log" id="log-box"></div>
  </div>
</div>

<script>
let PC, AC;
const PH = {l:[],d:[]};

function initCharts(){
  PC = new Chart(document.getElementById("pnlC").getContext("2d"),{
    type:"line",data:{labels:PH.l,datasets:[{data:PH.d,borderColor:"#00d4ff",backgroundColor:"rgba(0,212,255,0.05)",borderWidth:1.5,pointRadius:0,fill:true,tension:0.3}]},
    options:{responsive:true,animation:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:v=>(v.raw>=0?"+":"")+v.raw.toFixed(2)+" USDT"}}},
      scales:{x:{display:false},y:{grid:{color:"#1a2a3a"},ticks:{color:"#445",callback:v=>(v>=0?"+":"")+v.toFixed(1)+"$"}}}}
  });
  AC = new Chart(document.getElementById("allocC").getContext("2d"),{
    type:"doughnut",
    data:{labels:["Cash"],datasets:[{data:[100],backgroundColor:["#00d4ff","#00ff88","#f5a623","#ff4444","#aa44ff"],borderWidth:0}]},
    options:{responsive:true,animation:false,plugins:{legend:{position:"bottom",labels:{color:"#445",font:{size:10},boxWidth:8}}}}
  });
}
const f=(v,d=2)=>(v>=0?"+":"")+v.toFixed(d);
const cc=v=>v>=0?"g":"r";
const bar=(v,max,cls)=>`<div class="bar-bg"><div class="bar-fill ${cls}" style="width:${Math.min(100,Math.abs(v)/max*100).toFixed(0)}%;background:${cls==="g"?"#00ff88":"#ff4444"}"></div></div>`;

function update(){
  fetch("/api/data").then(r=>r.json()).then(d=>{
    if(!d.ok) return;
    document.getElementById("clock").textContent=new Date().toLocaleTimeString("fr-FR");

    // Ticker
    document.getElementById("ticker").innerHTML=Object.entries(d.market).map(([p,i])=>{
      const c=i.change_1m>=0?"#00ff88":"#ff4444";
      return `<span><b style="color:#aaa">${p}</b> <span style="color:${c}">${i.change_1m>=0?"&#9650;":"&#9660;"} ${i.price.toFixed(2)} <small>(${f(i.change_1m,2)}%)</small></span></span>`;
    }).join("");

    const p=d.portfolio;
    document.getElementById("k-total").textContent=p.total.toFixed(2)+" USDT";
    document.getElementById("k-total").className="big "+(p.pnl>=0?"g":"r");
    document.getElementById("k-roi").textContent=`ROI: ${f(p.roi)}% | Init: ${p.initial.toFixed(0)} USDT`;
    document.getElementById("k-pnl").textContent=f(p.pnl)+" USDT";
    document.getElementById("k-pnl").className="big "+(p.pnl>=0?"g":"r");
    document.getElementById("k-trades").textContent=`${p.total_trades} trades | ${p.cycles} cycles`;
    document.getElementById("k-wr").textContent=p.win_rate.toFixed(1)+"%";
    document.getElementById("k-wr").className="big "+(p.win_rate>=50?"g":"r");
    document.getElementById("k-wr-bar").style.width=p.win_rate+"%";
    document.getElementById("k-wrsub").textContent=`${p.wins}W / ${p.losses}L`;
    document.getElementById("k-pos").textContent=Object.keys(p.positions).length+" positions";
    document.getElementById("k-cash").textContent=`Cash: ${p.cash.toFixed(2)} | En jeu: ${p.in_pos.toFixed(2)} USDT`;

    // PnL chart
    PH.l.push(new Date().toLocaleTimeString("fr-FR"));
    PH.d.push(p.pnl);
    if(PH.l.length>200){PH.l.shift();PH.d.shift();}
    PC.data.datasets[0].borderColor=p.pnl>=0?"#00ff88":"#ff4444";
    PC.data.datasets[0].backgroundColor=p.pnl>=0?"rgba(0,255,136,0.05)":"rgba(255,68,68,0.05)";
    PC.update("none");

    // Alloc
    const al=["Cash"],av=[p.cash];
    Object.entries(p.positions).forEach(([s,pos])=>{al.push(s);av.push(pos.current_value);});
    AC.data.labels=al; AC.data.datasets[0].data=av; AC.update("none");

    // Marche
    document.getElementById("mkt-tb").innerHTML=Object.entries(d.market).map(([pair,i])=>{
      const c=i.change_1m>=0?"g":"r";
      const scls=i.signal==="BUY"?"tl":i.signal==="SELL"?"ts":"th";
      const slbl=i.signal==="BUY"?"&#9650; LONG":i.signal==="SELL"?"&#9660; SHORT":"&#9135; HOLD";
      const sc=(d.analysis[pair]||{}).total_score||0;
      return `<tr>
        <td><b>${pair}</b></td>
        <td class="${c}">${i.price.toFixed(2)}</td>
        <td class="${c}">${f(i.change_1m,3)}%</td>
        <td style="color:#556">${i.high.toFixed(2)}</td>
        <td style="color:#556">${i.low.toFixed(2)}</td>
        <td style="color:#445">${i.volume.toFixed(0)}</td>
        <td><span class="tag ${scls}">${slbl}</span></td>
        <td class="${cc(sc)}">${f(sc,1)}</td>
        <td>${bar(i.strength,1,c)}</td>
      </tr>`;
    }).join("") || '<tr><td colspan="9" style="color:#445;text-align:center">Chargement...</td></tr>';

    // Indicateurs techniques
    document.getElementById("ind-box").innerHTML=Object.entries(d.indicators).map(([pair,ind])=>{
      const rc=ind.rsi>70?"r":ind.rsi<30?"g":"y";
      const mc=ind.macd>=0?"g":"r";
      const bc=ind.bb_pct>0.8?"r":ind.bb_pct<0.2?"g":"w";
      const ac=ind.adx>30?"g":"y";
      return `<div style="margin-bottom:8px;padding-bottom:6px;border-bottom:1px solid #0d1520">
        <div style="color:#00d4ff;font-size:.76em;font-weight:600;margin-bottom:3px">${pair}</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:2px;font-size:.74em">
          <span style="color:#445">RSI14 <b class="${rc}">${ind.rsi.toFixed(1)}</b></span>
          <span style="color:#445">MACD <b class="${mc}">${ind.macd.toFixed(2)}</b></span>
          <span style="color:#445">ADX <b class="${ac}">${ind.adx.toFixed(1)}</b></span>
          <span style="color:#445">BB% <b class="${bc}">${(ind.bb_pct*100).toFixed(0)}%</b></span>
        </div>
      </div>`;
    }).join("");

    // Analyse approfondie
    document.getElementById("deep-box").innerHTML=Object.entries(d.analysis).map(([pair,a])=>{
      const sc=a.total_score||0; const c=cc(sc);
      const scores=[
        ["Tendance",a.trend_score,10],
        ["Momentum",a.momentum_score,10],
        ["Volume",a.volume_score,6],
        ["Patterns",a.pattern_score,6],
        ["Multi-TF",a.mtf_score,6]
      ];
      const sigHtml=(a.signals||[]).slice(0,4).map(s=>`<span class="tag th" style="margin:1px;font-size:.66em">${s}</span>`).join("");
      const patHtml=(a.patterns||[]).map(s=>`<span class="tag tl" style="margin:1px;font-size:.66em">${s}</span>`).join("");
      return `<div style="margin-bottom:10px;padding-bottom:8px;border-bottom:1px solid #0d1520">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px">
          <b style="color:#00d4ff">${pair}</b>
          <span class="tag ${sc>=4?"tl":sc<=-4?"ts":"th"}" style="font-size:.8em">${f(sc,1)} pts</span>
        </div>
        ${scores.map(([lbl,v,mx])=>`<div class="score-bar">
          <span class="score-label">${lbl}</span>
          <span class="score-val ${cc(v)}">${f(v,1)}</span>
          ${bar(v,mx,cc(v))}
        </div>`).join("")}
        <div style="margin-top:4px">${sigHtml}${patHtml}</div>
      </div>`;
    }).join("") || '<div style="color:#445">Chargement analyse...</div>';

    // Positions
    document.getElementById("pos-tb").innerHTML=Object.entries(p.positions).map(([sym,pos])=>{
      const c=cc(pos.pnl);
      return `<tr><td><b>${sym}</b></td><td><span class="tag ${pos.type==="short"?"ts":"tl'}">${pos.type.toUpperCase()}</span></td>
        <td>${pos.entry.toFixed(2)}</td><td class="${c}">${pos.current.toFixed(2)}</td>
        <td class="${c}">${f(pos.pnl)}</td><td class="${c}">${f(pos.pnl_pct)}%</td>
        <td class="r">${pos.sl.toFixed(2)}</td><td class="g">${pos.tp.toFixed(2)}</td></tr>`;
    }).join("") || '<tr><td colspan="8" style="color:#445;text-align:center;padding:8px">Aucune position</td></tr>';

    // Trades
    document.getElementById("trd-tb").innerHTML=[...d.trades].reverse().slice(0,8).map(t=>{
      const c=cc(t.pnl);
      return `<tr><td><b>${t.symbol}</b></td><td><span class="tag ${t.type==="short"?"ts":"tl'}">${t.type[0].toUpperCase()}</span></td>
        <td>${t.entry.toFixed(2)}</td><td>${t.exit.toFixed(2)}</td>
        <td class="${c}">${f(t.pnl)}</td><td class="${c}">${f(t.pnl_pct)}%</td>
        <td style="color:#445">${t.time}</td></tr>`;
    }).join("") || '<tr><td colspan="7" style="color:#445;text-align:center;padding:8px">Aucun trade</td></tr>';

    // Stats
    const s=d.stats;
    document.getElementById("stats-tb").innerHTML=[
      ["Profit moyen/trade",f(s.avg_pnl)+" USDT",cc(s.avg_pnl)],
      ["Meilleur trade","<span class=\'g\'>+"+s.best.toFixed(2)+" USDT</span>","g"],
      ["Pire trade","<span class=\'r\'>"+s.worst.toFixed(2)+" USDT</span>","r"],
      ["Profit Factor",s.pf.toFixed(2),s.pf>=1?"g":"r"],
      ["Sharpe Ratio",s.sharpe.toFixed(2),s.sharpe>=1?"g":"y"],
      ["Capital en position",s.invested.toFixed(2)+" USDT","w"],
      ["MAJ Marche",d.last_update||"--","b"],
    ].map(([k,v,c])=>`<tr><td style="color:#445">${k}</td><td style="text-align:right" class="${c}">${v}</td></tr>`).join("");

    // Log
    document.getElementById("log-box").innerHTML=[...(d.log||[])].reverse().slice(0,20)
      .map(l=>`<div class="logline">${l}</div>`).join("") || '<div class="logline" style="color:#334">Aucune activite</div>';

  }).catch(e=>console.warn("err:",e));
}

document.addEventListener("DOMContentLoaded",()=>{initCharts();update();setInterval(update,1000);});
</script>
</body></html>
'''

@app.route('/')
def index(): return render_template_string(HTML)

@app.route('/api/data')
def api_data():
    if not _portfolio: return jsonify({'ok':False})
    p = _portfolio
    market = _cache.get('market',{})
    indicators = _cache.get('indicators',{})
    analysis = _cache.get('analysis',{})

    pos_val = 0; positions_out = {}
    for sym, pos in p.positions.items():
        curr = market.get(sym,{}).get('price', pos['entry_price'])
        t = pos.get('trade_type','long')
        if t=='short':
            pnl=(pos['entry_price']-curr)*pos['amount']; pnl_pct=(pos['entry_price']-curr)/pos['entry_price']*100
            sl=pos['entry_price']*1.10; tp=pos['entry_price']*0.80
        else:
            pnl=(curr-pos['entry_price'])*pos['amount']; pnl_pct=(curr-pos['entry_price'])/pos['entry_price']*100
            sl=pos['entry_price']*0.90; tp=pos['entry_price']*1.20
        val=curr*pos['amount']; pos_val+=val
        positions_out[sym]={'entry':pos['entry_price'],'current':curr,'amount':pos['amount'],
            'pnl':round(pnl,2),'pnl_pct':round(pnl_pct,2),'current_value':round(val,2),
            'sl':round(sl,2),'tp':round(tp,2),'type':t}

    total=p.cash+pos_val; pnl_t=total-p.initial_capital; roi=pnl_t/p.initial_capital*100
    wins=sum(1 for t in p.trade_history if t['pnl']>0); losses=len(p.trade_history)-wins
    wr=wins/len(p.trade_history)*100 if p.trade_history else 0
    pnls=[t['pnl'] for t in p.trade_history]
    gains=sum(x for x in pnls if x>0); loss_sum=abs(sum(x for x in pnls if x<0))
    pf=gains/loss_sum if loss_sum>0 else 0
    try:
        import statistics
        sharpe=statistics.mean(pnls)/statistics.stdev(pnls) if len(pnls)>2 else 0
    except: sharpe=0

    trades_out=[{'symbol':t['symbol'],'entry':t['entry_price'],'exit':t['exit_price'],
        'pnl':round(t['pnl'],2),'pnl_pct':round(t.get('pnl_pct',0),2),
        'time':t['exit_time'].strftime('%H:%M:%S') if 'exit_time' in t else '--',
        'type':t.get('trade_type','long')} for t in p.trade_history]

    return jsonify({'ok':True,
        'portfolio':{'total':round(total,2),'cash':round(p.cash,2),'pnl':round(pnl_t,2),
            'roi':round(roi,2),'initial':p.initial_capital,'in_pos':round(pos_val,2),
            'total_trades':len(p.trade_history),'wins':wins,'losses':losses,'win_rate':round(wr,1),
            'positions':positions_out,'cycles':getattr(p,'cycles',0)},
        'market':market,'indicators':indicators,'analysis':analysis,'trades':trades_out,
        'stats':{'avg_pnl':sum(pnls)/len(pnls) if pnls else 0,'best':max(pnls) if pnls else 0,
            'worst':min(pnls) if pnls else 0,'pf':pf,'sharpe':sharpe,'invested':round(pos_val,2)},
        'log':getattr(p,'activity_log',[]),'last_update':_cache.get('last_update','--')})

def run_dashboard(portfolio, exchange):
    global _portfolio, _exchange
    _portfolio=portfolio; _exchange=exchange
    threading.Thread(target=_update_cache, daemon=True).start()
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
