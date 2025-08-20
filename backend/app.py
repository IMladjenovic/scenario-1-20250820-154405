from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import sqlite3
import threading
import time
import random
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fx_trading_secret_key'
CORS(app, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*")

# Database initialization
def init_db():
    conn = sqlite3.connect('fx_trading.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS currency_pairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            base_currency TEXT NOT NULL,
            quote_currency TEXT NOT NULL,
            current_rate REAL NOT NULL,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(base_currency, quote_currency)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair_id INTEGER,
            trade_type TEXT NOT NULL,
            amount REAL NOT NULL,
            rate REAL NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pair_id) REFERENCES currency_pairs (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            currency TEXT NOT NULL UNIQUE,
            balance REAL NOT NULL DEFAULT 0
        )
    ''')
    
    # Insert initial currency pairs
    pairs = [
        ('EUR', 'USD', 1.0850),
        ('GBP', 'USD', 1.2650),
        ('USD', 'JPY', 149.50),
        ('AUD', 'USD', 0.6450),
        ('USD', 'CHF', 0.8950),
        ('EUR', 'GBP', 0.8580)
    ]
    
    for base, quote, rate in pairs:
        cursor.execute('''
            INSERT OR IGNORE INTO currency_pairs (base_currency, quote_currency, current_rate)
            VALUES (?, ?, ?)
        ''', (base, quote, rate))
    
    # Initialize portfolio with some starting balances
    initial_balances = [
        ('USD', 10000.0),
        ('EUR', 5000.0),
        ('GBP', 3000.0),
        ('JPY', 500000.0),
        ('AUD', 8000.0),
        ('CHF', 7000.0)
    ]
    
    for currency, balance in initial_balances:
        cursor.execute('''
            INSERT OR IGNORE INTO portfolio (currency, balance)
            VALUES (?, ?)
        ''', (currency, balance))
    
    conn.commit()
    conn.close()

# API Routes
@app.route('/api/currency-pairs', methods=['GET'])
def get_currency_pairs():
    conn = sqlite3.connect('fx_trading.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, base_currency, quote_currency, current_rate, last_updated
        FROM currency_pairs
    ''')
    pairs = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': pair[0],
        'base_currency': pair[1],
        'quote_currency': pair[2],
        'current_rate': pair[3],
        'last_updated': pair[4],
        'pair_name': f"{pair[1]}/{pair[2]}"
    } for pair in pairs])

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    conn = sqlite3.connect('fx_trading.db')
    cursor = conn.cursor()
    cursor.execute('SELECT currency, balance FROM portfolio WHERE balance > 0')
    portfolio = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'currency': item[0],
        'balance': item[1]
    } for item in portfolio])

@app.route('/api/trade', methods=['POST'])
def execute_trade():
    data = request.json
    pair_id = data.get('pair_id')
    trade_type = data.get('trade_type')  # 'buy' or 'sell'
    amount_str = data.get('amount')
    
    # Validate required fields
    if not pair_id:
        return jsonify({'error': 'Currency pair ID is required'}), 400
    
    if not trade_type or trade_type not in ['buy', 'sell']:
        return jsonify({'error': 'Valid trade type (buy/sell) is required'}), 400
    
    if not amount_str:
        return jsonify({'error': 'Amount is required'}), 400
    
    try:
        amount = float(amount_str)
        if amount <= 0:
            return jsonify({'error': 'Amount must be greater than 0'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid amount format'}), 400
    
    conn = sqlite3.connect('fx_trading.db')
    cursor = conn.cursor()
    
    # Get currency pair info
    cursor.execute('''
        SELECT base_currency, quote_currency, current_rate
        FROM currency_pairs WHERE id = ?
    ''', (pair_id,))
    pair_info = cursor.fetchone()
    
    if not pair_info:
        conn.close()
        return jsonify({'error': 'Currency pair not found'}), 404
    
    base_currency, quote_currency, current_rate = pair_info
    
    # Calculate trade amounts
    if trade_type == 'buy':
        # Buying base currency with quote currency
        quote_amount_needed = amount * current_rate
        
        # Check if user has enough quote currency
        cursor.execute('SELECT balance FROM portfolio WHERE currency = ?', (quote_currency,))
        quote_balance = cursor.fetchone()
        
        if not quote_balance or quote_balance[0] < quote_amount_needed:
            conn.close()
            return jsonify({'error': f'Insufficient {quote_currency} balance'}), 400
        
        # Update balances
        cursor.execute('''
            UPDATE portfolio SET balance = balance - ? WHERE currency = ?
        ''', (quote_amount_needed, quote_currency))
        
        cursor.execute('''
            INSERT OR IGNORE INTO portfolio (currency, balance) VALUES (?, 0)
        ''', (base_currency,))
        
        cursor.execute('''
            UPDATE portfolio SET balance = balance + ? WHERE currency = ?
        ''', (amount, base_currency))
        
    else:  # sell
        # Selling base currency for quote currency
        # Check if user has enough base currency
        cursor.execute('SELECT balance FROM portfolio WHERE currency = ?', (base_currency,))
        base_balance = cursor.fetchone()
        
        if not base_balance or base_balance[0] < amount:
            conn.close()
            return jsonify({'error': f'Insufficient {base_currency} balance'}), 400
        
        quote_amount_received = amount * current_rate
        
        # Update balances
        cursor.execute('''
            UPDATE portfolio SET balance = balance - ? WHERE currency = ?
        ''', (amount, base_currency))
        
        cursor.execute('''
            INSERT OR IGNORE INTO portfolio (currency, balance) VALUES (?, 0)
        ''', (quote_currency,))
        
        cursor.execute('''
            UPDATE portfolio SET balance = balance + ? WHERE currency = ?
        ''', (quote_amount_received, quote_currency))
    
    # Record the trade
    cursor.execute('''
        INSERT INTO trades (pair_id, trade_type, amount, rate)
        VALUES (?, ?, ?, ?)
    ''', (pair_id, trade_type, amount, current_rate))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'success': True,
        'message': f'Trade executed: {trade_type} {amount} {base_currency}',
        'rate': current_rate
    })

@app.route('/api/trades', methods=['GET'])
def get_trades():
    conn = sqlite3.connect('fx_trading.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, cp.base_currency, cp.quote_currency, t.trade_type, 
               t.amount, t.rate, t.timestamp
        FROM trades t
        JOIN currency_pairs cp ON t.pair_id = cp.id
        ORDER BY t.timestamp DESC
        LIMIT 50
    ''')
    trades = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': trade[0],
        'pair': f"{trade[1]}/{trade[2]}",
        'type': trade[3],
        'amount': trade[4],
        'rate': trade[5],
        'timestamp': trade[6]
    } for trade in trades])

# Real-time rate updates
def update_rates():
    while True:
        time.sleep(5)  # Update every 5 seconds
        
        conn = sqlite3.connect('fx_trading.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, base_currency, quote_currency, current_rate FROM currency_pairs')
        pairs = cursor.fetchall()
        
        updated_pairs = []
        for pair in pairs:
            pair_id, base, quote, current_rate = pair
            # Simulate rate fluctuation (±0.5%)
            change_percent = random.uniform(-0.005, 0.005)
            new_rate = current_rate * (1 + change_percent)
            new_rate = round(new_rate, 4)
            
            cursor.execute('''
                UPDATE currency_pairs SET current_rate = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (new_rate, pair_id))
            
            updated_pairs.append({
                'id': pair_id,
                'pair_name': f"{base}/{quote}",
                'current_rate': new_rate,
                'change': change_percent * 100
            })
        
        conn.commit()
        conn.close()
        
        # Emit updates to connected clients
        socketio.emit('rate_update', {'pairs': updated_pairs})

# WebSocket events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'message': 'Connected to FX trading server'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    init_db()
    
    # Start rate update thread
    rate_thread = threading.Thread(target=update_rates, daemon=True)
    rate_thread.start()
    
    socketio.run(app, host='0.0.0.0', port=12000, debug=True)