# FX Trading Application

A modern, real-time Foreign Exchange (FX) trading platform built with Python Flask backend and vanilla JavaScript frontend.

## Features

- **Real-time Exchange Rates**: Live currency pair rates with automatic updates every 5 seconds
- **Portfolio Management**: Track your currency balances across multiple currencies
- **Trading Operations**: Execute buy and sell trades with real-time rate calculations
- **Trade History**: View your recent trading activity
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **WebSocket Integration**: Real-time updates without page refresh

## Tech Stack

### Backend
- **Python 3.12+** with Flask web framework
- **SQLite** database for data persistence
- **Flask-SocketIO** for real-time WebSocket communication
- **Flask-CORS** for cross-origin resource sharing

### Frontend
- **HTML5/CSS3** with modern responsive design
- **Vanilla JavaScript** with WebSocket client
- **Chart.js** ready for future chart implementations

## Project Structure

```
fx-trading-app/
├── backend/
│   └── app.py              # Flask application with API endpoints
├── frontend/
│   ├── index.html          # Main application interface
│   ├── style.css           # Responsive styling
│   └── app.js              # Frontend JavaScript logic
├── tests/
│   ├── test_backend.py     # Backend API tests
│   └── test_frontend.py    # Frontend integration tests
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation & Setup

### Prerequisites
- Python 3.12 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fx-trading-app
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the backend server**
   ```bash
   cd backend
   python app.py
   ```
   The server will start on `http://localhost:12000`

4. **Open the frontend**
   Open `frontend/index.html` in your web browser, or serve it through a local web server:
   ```bash
   cd frontend
   python -m http.server 8080
   ```
   Then visit `http://localhost:8080`

## API Documentation

### Base URL
```
http://localhost:12000/api
```

### Endpoints

#### GET /currency-pairs
Get all available currency pairs with current rates.

**Response:**
```json
[
  {
    "id": 1,
    "base_currency": "EUR",
    "quote_currency": "USD",
    "current_rate": 1.0850,
    "last_updated": "2025-08-20 14:30:00",
    "pair_name": "EUR/USD"
  }
]
```

#### GET /portfolio
Get current portfolio balances.

**Response:**
```json
[
  {
    "currency": "USD",
    "balance": 10000.00
  },
  {
    "currency": "EUR",
    "balance": 5000.00
  }
]
```

#### POST /trade
Execute a buy or sell trade.

**Request Body:**
```json
{
  "pair_id": 1,
  "trade_type": "buy",
  "amount": 100.0
}
```

**Response:**
```json
{
  "success": true,
  "message": "Trade executed: buy 100.0 EUR",
  "rate": 1.0850
}
```

#### GET /trades
Get recent trade history (last 50 trades).

**Response:**
```json
[
  {
    "id": 1,
    "pair": "EUR/USD",
    "type": "buy",
    "amount": 100.0,
    "rate": 1.0850,
    "timestamp": "2025-08-20 14:30:00"
  }
]
```

### WebSocket Events

#### Connection
- **Event**: `connect`
- **Description**: Establishes WebSocket connection

#### Rate Updates
- **Event**: `rate_update`
- **Description**: Broadcasts real-time rate changes
- **Data Format**:
```json
{
  "pairs": [
    {
      "id": 1,
      "pair_name": "EUR/USD",
      "current_rate": 1.0852,
      "change": 0.18
    }
  ]
}
```

## Currency Pairs

The application supports the following major currency pairs:

- **EUR/USD** - Euro to US Dollar
- **GBP/USD** - British Pound to US Dollar  
- **USD/JPY** - US Dollar to Japanese Yen
- **AUD/USD** - Australian Dollar to US Dollar
- **USD/CHF** - US Dollar to Swiss Franc
- **EUR/GBP** - Euro to British Pound

## Trading Logic

### Buy Orders
- Deducts quote currency from portfolio
- Adds base currency to portfolio
- Amount calculation: `quote_needed = base_amount * current_rate`

### Sell Orders
- Deducts base currency from portfolio
- Adds quote currency to portfolio
- Amount calculation: `quote_received = base_amount * current_rate`

### Portfolio Management
- Automatic balance updates after each trade
- Insufficient balance validation
- Multi-currency support

## Testing

Run the test suite to verify functionality:

```bash
# Run backend tests
python -m pytest tests/test_backend.py -v

# Run all tests
python -m pytest tests/ -v
```

### Test Coverage
- **API Endpoints**: All REST endpoints tested
- **Trading Logic**: Buy/sell calculations and validations
- **Database Operations**: CRUD operations and data integrity
- **Error Handling**: Invalid inputs and edge cases

## Development

### Adding New Currency Pairs
1. Update the `pairs` list in `backend/app.py` in the `init_db()` function
2. Restart the application to initialize new pairs

### Customizing Rate Updates
- Modify the `update_rates()` function in `backend/app.py`
- Adjust the update interval (default: 5 seconds)
- Change the volatility range (default: ±0.5%)

### Frontend Customization
- Modify `frontend/style.css` for styling changes
- Update `frontend/app.js` for functionality changes
- Responsive breakpoints defined for mobile/tablet views

## Production Deployment

### Environment Variables
Set the following environment variables for production:

```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here
export DATABASE_URL=your-database-url
```

### Database Migration
For production, consider migrating from SQLite to PostgreSQL:

1. Install PostgreSQL adapter: `pip install psycopg2`
2. Update database connection in `app.py`
3. Run database initialization

### Security Considerations
- Implement user authentication
- Add API rate limiting
- Use HTTPS in production
- Validate and sanitize all inputs
- Implement proper error logging

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation above
- Review the test files for usage examples
