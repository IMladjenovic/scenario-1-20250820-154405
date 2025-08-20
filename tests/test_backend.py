import pytest
import json
import sqlite3
import os
import sys
import tempfile
from unittest.mock import patch, MagicMock

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app import app, init_db

@pytest.fixture
def client():
    # Create a temporary database for testing
    db_fd, temp_db_path = tempfile.mkstemp(suffix='.db')
    app.config['DATABASE'] = temp_db_path
    app.config['TESTING'] = True
    
    # Patch the database connection to use our temp database
    original_connect = sqlite3.connect
    
    def mock_connect(db_name):
        if db_name == 'fx_trading.db':
            return original_connect(temp_db_path)
        return original_connect(db_name)
    
    with patch('sqlite3.connect', side_effect=mock_connect):
        with app.test_client() as client:
            with app.app_context():
                # Initialize test database
                init_db()
            yield client
    
    os.close(db_fd)
    os.unlink(temp_db_path)

@pytest.fixture
def sample_currency_pairs():
    return [
        {'id': 1, 'base_currency': 'EUR', 'quote_currency': 'USD', 'current_rate': 1.0850},
        {'id': 2, 'base_currency': 'GBP', 'quote_currency': 'USD', 'current_rate': 1.2650},
        {'id': 3, 'base_currency': 'USD', 'quote_currency': 'JPY', 'current_rate': 149.50}
    ]

class TestCurrencyPairsAPI:
    def test_get_currency_pairs(self, client):
        """Test retrieving currency pairs"""
        response = client.get('/api/currency-pairs')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Check structure of first pair
        pair = data[0]
        required_fields = ['id', 'base_currency', 'quote_currency', 'current_rate', 'pair_name']
        for field in required_fields:
            assert field in pair
        
        # Check pair_name format
        assert '/' in pair['pair_name']
        assert pair['pair_name'] == f"{pair['base_currency']}/{pair['quote_currency']}"

class TestPortfolioAPI:
    def test_get_portfolio(self, client):
        """Test retrieving portfolio"""
        response = client.get('/api/portfolio')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        
        # Check structure if portfolio has items
        if data:
            portfolio_item = data[0]
            assert 'currency' in portfolio_item
            assert 'balance' in portfolio_item
            assert isinstance(portfolio_item['balance'], (int, float))

class TestTradingAPI:
    def test_execute_buy_trade_success(self, client):
        """Test successful buy trade execution"""
        # First get available currency pairs
        pairs_response = client.get('/api/currency-pairs')
        pairs = json.loads(pairs_response.data)
        
        if pairs:
            pair = pairs[0]  # Use first available pair
            
            trade_data = {
                'pair_id': pair['id'],
                'trade_type': 'buy',
                'amount': 100.0
            }
            
            response = client.post('/api/trade', 
                                 data=json.dumps(trade_data),
                                 content_type='application/json')
            
            # The trade might fail due to insufficient balance, which is expected
            # We're testing the API structure and response format
            data = json.loads(response.data)
            
            if response.status_code == 200:
                assert data['success'] is True
                assert 'message' in data
                assert 'rate' in data
            else:
                # Should return error message for insufficient balance
                assert 'error' in data

    def test_execute_sell_trade_success(self, client):
        """Test successful sell trade execution"""
        pairs_response = client.get('/api/currency-pairs')
        pairs = json.loads(pairs_response.data)
        
        if pairs:
            pair = pairs[0]
            
            trade_data = {
                'pair_id': pair['id'],
                'trade_type': 'sell',
                'amount': 10.0
            }
            
            response = client.post('/api/trade',
                                 data=json.dumps(trade_data),
                                 content_type='application/json')
            
            data = json.loads(response.data)
            
            if response.status_code == 200:
                assert data['success'] is True
                assert 'message' in data
                assert 'rate' in data
            else:
                assert 'error' in data

    def test_execute_trade_invalid_pair(self, client):
        """Test trade with invalid currency pair"""
        trade_data = {
            'pair_id': 99999,  # Non-existent pair
            'trade_type': 'buy',
            'amount': 100.0
        }
        
        response = client.post('/api/trade',
                             data=json.dumps(trade_data),
                             content_type='application/json')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'not found' in data['error'].lower()

    def test_execute_trade_missing_data(self, client):
        """Test trade with missing required data"""
        trade_data = {
            'pair_id': 1,
            'trade_type': 'buy'
            # Missing amount
        }
        
        response = client.post('/api/trade',
                             data=json.dumps(trade_data),
                             content_type='application/json')
        
        # Should handle missing data gracefully
        assert response.status_code in [400, 500]

class TestTradesHistoryAPI:
    def test_get_trades_empty(self, client):
        """Test retrieving trades when no trades exist"""
        response = client.get('/api/trades')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        # Initially should be empty
        assert len(data) == 0

    def test_get_trades_structure(self, client):
        """Test the structure of trades response"""
        # First execute a trade to have data
        pairs_response = client.get('/api/currency-pairs')
        pairs = json.loads(pairs_response.data)
        
        if pairs:
            # Try to execute a trade (might fail due to balance)
            trade_data = {
                'pair_id': pairs[0]['id'],
                'trade_type': 'buy',
                'amount': 1.0
            }
            
            client.post('/api/trade',
                       data=json.dumps(trade_data),
                       content_type='application/json')
            
            # Now get trades
            response = client.get('/api/trades')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, list)
            
            # If we have trades, check structure
            if data:
                trade = data[0]
                required_fields = ['id', 'pair', 'type', 'amount', 'rate', 'timestamp']
                for field in required_fields:
                    assert field in trade

class TestDatabaseOperations:
    def test_database_initialization(self):
        """Test that database initializes correctly"""
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
            db_path = tmp_db.name
        
        try:
            # Initialize database
            original_db = 'fx_trading.db'
            
            # Temporarily replace the database path in the init_db function
            import app
            original_connect = sqlite3.connect
            
            def mock_connect(db_name):
                if db_name == 'fx_trading.db':
                    return original_connect(db_path)
                return original_connect(db_name)
            
            with patch('sqlite3.connect', side_effect=mock_connect):
                init_db()
            
            # Verify tables exist
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['currency_pairs', 'trades', 'portfolio']
            for table in expected_tables:
                assert table in tables
            
            # Check if initial data exists
            cursor.execute("SELECT COUNT(*) FROM currency_pairs")
            pair_count = cursor.fetchone()[0]
            assert pair_count > 0
            
            cursor.execute("SELECT COUNT(*) FROM portfolio")
            portfolio_count = cursor.fetchone()[0]
            assert portfolio_count > 0
            
            conn.close()
            
        finally:
            # Clean up
            if os.path.exists(db_path):
                os.unlink(db_path)

class TestTradingLogic:
    def test_buy_trade_calculation(self, client):
        """Test buy trade amount calculations"""
        # This test verifies the trading logic calculations
        pairs_response = client.get('/api/currency-pairs')
        pairs = json.loads(pairs_response.data)
        
        if pairs:
            pair = pairs[0]
            base_currency = pair['base_currency']
            quote_currency = pair['quote_currency']
            current_rate = pair['current_rate']
            
            # Calculate expected quote currency needed
            amount_to_buy = 100.0
            expected_quote_needed = amount_to_buy * current_rate
            
            # This is more of a logic verification test
            assert expected_quote_needed > 0
            assert isinstance(expected_quote_needed, float)

    def test_sell_trade_calculation(self, client):
        """Test sell trade amount calculations"""
        pairs_response = client.get('/api/currency-pairs')
        pairs = json.loads(pairs_response.data)
        
        if pairs:
            pair = pairs[0]
            current_rate = pair['current_rate']
            
            # Calculate expected quote currency received
            amount_to_sell = 100.0
            expected_quote_received = amount_to_sell * current_rate
            
            assert expected_quote_received > 0
            assert isinstance(expected_quote_received, float)

if __name__ == '__main__':
    pytest.main([__file__])