from flask import Flask, jsonify, render_template_string
import logging

logger = logging.getLogger(__name__)

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 Crypto Trading Bot Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0a0e1a; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; }
        .header { background: linear-gradient(135deg, #1a1f3a, #0d1117); padding: 20px 30px; border-bottom: 1px solid #00ff88; }
        .header h1 { color: #00ff88; font-size: 1.8em; }
        .header span { color: #888; font-size: 0.9em; }
        .container { padding: 30px; max-width: 1200px; margin: 0 auto; }
        .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 20px; margin-bottom: 30px; }
        .card { background: #1a1f3a; border: 1px solid #2a3060; border-radius: 12px; padding: 20px; }
        .card .label { color: #888; font-size: 0.85em; margin-bottom: 8px; }
        .card .value { font-size: 2em; font-weight: bold; }
        .positive { color: #00ff88; }
        .negative { color: #ff4444; }
        .neutral { color: #4fc3f7; }
        .section { background: #1a1f3a; border: 1px solid #2a3060; border-radius: 12px; padding: 20px; margin-bottom: 20px; }
        .section h2 { color: #00ff88; margin-bottom: 15px; font-size: 1.1em; }
        table { width: 100%; border-collapse: collapse; }
        th { color: #888; font-size: 0.8em; padding: 8px 12px; text-align: left; border-bottom: 1px solid #2a3060; }
        td { padding: 10px 12px; border-bottom: 1px solid #15192e; font-size: 0.9em; }
        tr:hover { background: #1e2444; }
        .badge { padding: 3px 8px; border-radius: 4px; font-size: 0.75em; font-weight: bold; }
        .badge-buy { background: #00ff8822; color: #00ff88; border: 1px solid #00ff88; }
        .badge-sell { background: #ff444422; color: #ff4444; border: 1px solid #ff4444; }
        .mode-badge { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: bold; }
        .mode-paper { background: #ffa50022; color: #ffa500; border: 1px solid #ffa500; }
        .mode-live { background: #ff000022; color: #ff4444; border: 1px solid #ff4444; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI Crypto Trading Bot</h1>
        <span id="last-update">Chargement...</span>
    </div>
    <div class="container">
        <div class="cards" id="cards">
            <div class="card"><div class="label">💰 Capital Total</div><div class="value neutral" id="total">---</div></div>
            <div class="card"><div class="label">📈 ROI</div><div class="value" id="roi">---</div></div>
            <div class="card"><div class="label">💵 Cash Disponible</div><div class="value neutral" id="cash">---</div></div>
            <div class="card"><div class="label">🎯 Win Rate</div><div class="value" id="winrate">---</div></div>
            <div class="card"><div class="label">📊 Total Trades</div><div class="value neutral" id="trades">---</div></div>
            <div class="card"><div class="label">⚡ Mode</div><div class="value" id="mode">---</div></div>
        </div>
        <div class="section">
            <h2>📈 Positions Ouvertes</h2>
            <table><thead><tr><th>Paire</th><th>Amount</th><th>Prix Entrée</th><th>Plus Haut</th><th>PnL Estimé</th></tr></thead>
            <tbody id="positions"><tr><td colspan="5" style="color:#888;text-align:center">Aucune position ouverte</td></tr></tbody></table>
        </div>
        <div class="section">
            <h2>📝 Historique des Trades</h2>
            <table><thead><tr><th>Paire</th><th>Entrée</th><th>Sortie</th><th>PnL</th><th>%</th><th>Type</th></tr></thead>
            <tbody id="history"><tr><td colspan="6" style="color:#888;text-align:center">Aucun trade encore</td></tr></tbody></table>
        </div>
    </div>
    <script>
        async function update() {
            try {
                const r = await fetch('/api/status');
                const d = await r.json();
                document.getElementById('total').textContent = d.total_value.toFixed(2) + ' USDT';
                document.getElementById('roi').textContent = (d.roi >= 0 ? '+' : '') + d.roi.toFixed(2) + '%';
                document.getElementById('roi').className = 'value ' + (d.roi >= 0 ? 'positive' : 'negative');
                document.getElementById('cash').textContent = d.cash.toFixed(2) + ' USDT';
                document.getElementById('winrate').textContent = d.win_rate.toFixed(1) + '%';
                document.getElementById('winrate').className = 'value ' + (d.win_rate >= 50 ? 'positive' : 'negative');
                document.getElementById('trades').textContent = d.total_trades;
                document.getElementById('mode').innerHTML = `<span class="mode-badge mode-${d.mode}">${d.mode.toUpperCase()}</span>`;
                document.getElementById('last-update').textContent = 'Mis à jour: ' + new Date().toLocaleTimeString('fr-FR');
                
                const posBody = document.getElementById('positions');
                posBody.innerHTML = d.positions.length ? d.positions.map(p => `<tr><td>${p.symbol}</td><td>${p.amount}</td><td>${p.entry_price}</td><td>${p.highest_price}</td><td class="${p.pnl >= 0 ? 'positive' : 'negative'}">${p.pnl >= 0 ? '+' : ''}${p.pnl.toFixed(2)}</td></tr>`).join('') : '<tr><td colspan="5" style="color:#888;text-align:center">Aucune position</td></tr>';
                
                const histBody = document.getElementById('history');
                histBody.innerHTML = d.history.length ? d.history.slice().reverse().slice(0,20).map(t => `<tr><td>${t.symbol}</td><td>${t.entry_price}</td><td>${t.exit_price}</td><td class="${t.pnl >= 0 ? 'positive' : 'negative'}">${t.pnl >= 0 ? '+' : ''}${t.pnl.toFixed(2)}</td><td class="${t.pnl_pct >= 0 ? 'positive' : 'negative'}">${t.pnl_pct.toFixed(2)}%</td><td><span class="badge ${t.pnl >= 0 ? 'badge-buy' : 'badge-sell'}">${t.pnl >= 0 ? 'PROFIT' : 'LOSS'}</span></td></tr>`).join('') : '<tr><td colspan="6" style="color:#888;text-align:center">Aucun trade</td></tr>';
            } catch(e) { console.error(e); }
        }
        update();
        setInterval(update, 5000);
    </script>
</body>
</html>
'''

app = Flask(__name__)
_portfolio = None
_exchange = None

@app.route('/')
def index():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/status')
def status():
    import os
    if _portfolio is None:
        return jsonify({'error': 'Portfolio non initialisé'})
    
    positions_data = []
    for sym, pos in _portfolio.positions.items():
        estimated_pnl = 0
        positions_data.append({
            'symbol': sym,
            'amount': round(pos['amount'], 6),
            'entry_price': round(pos['entry_price'], 4),
            'highest_price': round(pos.get('highest_price', pos['entry_price']), 4),
            'pnl': estimated_pnl
        })
    
    history_data = [{
        'symbol': t['symbol'],
        'entry_price': round(t['entry_price'], 4),
        'exit_price': round(t['exit_price'], 4),
        'pnl': round(t['pnl'], 2),
        'pnl_pct': round(t['pnl_pct'], 2)
    } for t in _portfolio.trade_history]
    
    total = _portfolio.get_total_value()
    roi = (total - _portfolio.initial_capital) / _portfolio.initial_capital * 100
    
    return jsonify({
        'total_value': round(total, 2),
        'cash': round(_portfolio.cash, 2),
        'roi': round(roi, 2),
        'total_pnl': round(_portfolio.total_pnl, 2),
        'win_rate': round(_portfolio.get_win_rate(), 1),
        'total_trades': len(_portfolio.trade_history),
        'positions': positions_data,
        'history': history_data,
        'mode': os.getenv('TRADING_MODE', 'paper')
    })

def run_dashboard(portfolio, exchange):
    global _portfolio, _exchange
    _portfolio = portfolio
    _exchange = exchange
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
