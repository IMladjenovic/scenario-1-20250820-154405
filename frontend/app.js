class FXTradingApp {
    constructor() {
        this.socket = null;
        this.currencyPairs = [];
        this.portfolio = [];
        this.trades = [];
        
        this.init();
    }
    
    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.loadInitialData();
    }
    
    connectWebSocket() {
        // Connect to the Flask-SocketIO server
        this.socket = io('http://localhost:12000');
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('rate_update', (data) => {
            this.handleRateUpdate(data);
        });
        
        this.socket.on('connected', (data) => {
            console.log('Server message:', data.message);
        });
    }
    
    updateConnectionStatus(connected) {
        const indicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (connected) {
            indicator.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            indicator.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    }
    
    async loadInitialData() {
        try {
            await Promise.all([
                this.loadCurrencyPairs(),
                this.loadPortfolio(),
                this.loadRecentTrades()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }
    
    async loadCurrencyPairs() {
        try {
            const response = await fetch('http://localhost:12000/api/currency-pairs');
            this.currencyPairs = await response.json();
            this.renderCurrencyPairs();
            this.populateTradePairSelect();
        } catch (error) {
            console.error('Error loading currency pairs:', error);
        }
    }
    
    async loadPortfolio() {
        try {
            const response = await fetch('http://localhost:12000/api/portfolio');
            this.portfolio = await response.json();
            this.renderPortfolio();
        } catch (error) {
            console.error('Error loading portfolio:', error);
        }
    }
    
    async loadRecentTrades() {
        try {
            const response = await fetch('http://localhost:12000/api/trades');
            this.trades = await response.json();
            this.renderRecentTrades();
        } catch (error) {
            console.error('Error loading recent trades:', error);
        }
    }
    
    renderPortfolio() {
        const portfolioGrid = document.getElementById('portfolioGrid');
        portfolioGrid.innerHTML = '';
        
        this.portfolio.forEach(item => {
            const portfolioItem = document.createElement('div');
            portfolioItem.className = 'portfolio-item';
            portfolioItem.innerHTML = `
                <div class="currency">${item.currency}</div>
                <div class="balance">${this.formatNumber(item.balance)}</div>
            `;
            portfolioGrid.appendChild(portfolioItem);
        });
    }
    
    renderCurrencyPairs() {
        const ratesGrid = document.getElementById('ratesGrid');
        ratesGrid.innerHTML = '';
        
        this.currencyPairs.forEach(pair => {
            const rateItem = document.createElement('div');
            rateItem.className = 'rate-item';
            rateItem.id = `pair-${pair.id}`;
            rateItem.innerHTML = `
                <div class="pair-name">${pair.pair_name}</div>
                <div class="rate-info">
                    <div class="current-rate">${this.formatRate(pair.current_rate)}</div>
                    <div class="rate-change" id="change-${pair.id}">--</div>
                </div>
            `;
            ratesGrid.appendChild(rateItem);
        });
    }
    
    populateTradePairSelect() {
        const select = document.getElementById('tradePair');
        select.innerHTML = '<option value="">Select a pair...</option>';
        
        this.currencyPairs.forEach(pair => {
            const option = document.createElement('option');
            option.value = pair.id;
            option.textContent = pair.pair_name;
            select.appendChild(option);
        });
    }
    
    renderRecentTrades() {
        const tradesList = document.getElementById('tradesList');
        tradesList.innerHTML = '';
        
        if (this.trades.length === 0) {
            tradesList.innerHTML = '<p style="text-align: center; color: #7f8c8d;">No trades yet</p>';
            return;
        }
        
        this.trades.forEach(trade => {
            const tradeItem = document.createElement('div');
            tradeItem.className = 'trade-item';
            tradeItem.innerHTML = `
                <div class="trade-info">
                    <div class="trade-pair">${trade.pair}</div>
                    <div class="trade-details">
                        ${this.formatNumber(trade.amount)} @ ${this.formatRate(trade.rate)}
                        <br>
                        <small>${this.formatDateTime(trade.timestamp)}</small>
                    </div>
                </div>
                <div class="trade-type ${trade.type}">${trade.type}</div>
            `;
            tradesList.appendChild(tradeItem);
        });
    }
    
    handleRateUpdate(data) {
        data.pairs.forEach(pair => {
            const pairElement = document.getElementById(`pair-${pair.id}`);
            const changeElement = document.getElementById(`change-${pair.id}`);
            
            if (pairElement && changeElement) {
                // Update rate
                const rateElement = pairElement.querySelector('.current-rate');
                rateElement.textContent = this.formatRate(pair.current_rate);
                
                // Update change indicator
                const changePercent = pair.change;
                const changeText = `${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(2)}%`;
                changeElement.textContent = changeText;
                
                // Update styling based on change
                pairElement.classList.remove('positive', 'negative');
                changeElement.classList.remove('positive', 'negative');
                
                if (changePercent > 0) {
                    pairElement.classList.add('positive');
                    changeElement.classList.add('positive');
                } else if (changePercent < 0) {
                    pairElement.classList.add('negative');
                    changeElement.classList.add('negative');
                }
                
                // Update currency pairs data
                const pairIndex = this.currencyPairs.findIndex(p => p.id === pair.id);
                if (pairIndex !== -1) {
                    this.currencyPairs[pairIndex].current_rate = pair.current_rate;
                }
            }
        });
    }
    
    setupEventListeners() {
        const executeTradeBtn = document.getElementById('executeTradeBtn');
        executeTradeBtn.addEventListener('click', () => this.executeTrade());
        
        // Enable Enter key for trade execution
        document.getElementById('tradeAmount').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.executeTrade();
            }
        });
    }
    
    async executeTrade() {
        const pairId = document.getElementById('tradePair').value;
        const tradeType = document.getElementById('tradeType').value;
        const amount = parseFloat(document.getElementById('tradeAmount').value);
        const resultDiv = document.getElementById('tradeResult');
        
        // Validation
        if (!pairId) {
            this.showTradeResult('Please select a currency pair', 'error');
            return;
        }
        
        if (!amount || amount <= 0) {
            this.showTradeResult('Please enter a valid amount', 'error');
            return;
        }
        
        // Disable button during trade execution
        const executeBtn = document.getElementById('executeTradeBtn');
        executeBtn.disabled = true;
        executeBtn.textContent = 'Executing...';
        
        try {
            const response = await fetch('http://localhost:12000/api/trade', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    pair_id: parseInt(pairId),
                    trade_type: tradeType,
                    amount: amount
                })
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showTradeResult(result.message, 'success');
                // Refresh data after successful trade
                await this.loadPortfolio();
                await this.loadRecentTrades();
                // Clear form
                document.getElementById('tradeAmount').value = '';
            } else {
                this.showTradeResult(result.error || 'Trade failed', 'error');
            }
        } catch (error) {
            console.error('Trade execution error:', error);
            this.showTradeResult('Network error occurred', 'error');
        } finally {
            // Re-enable button
            executeBtn.disabled = false;
            executeBtn.textContent = 'Execute Trade';
        }
    }
    
    showTradeResult(message, type) {
        const resultDiv = document.getElementById('tradeResult');
        resultDiv.textContent = message;
        resultDiv.className = `trade-result ${type}`;
        resultDiv.style.display = 'block';
        
        // Hide after 5 seconds
        setTimeout(() => {
            resultDiv.style.display = 'none';
        }, 5000);
    }
    
    formatNumber(num) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(num);
    }
    
    formatRate(rate) {
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 4,
            maximumFractionDigits: 4
        }).format(rate);
    }
    
    formatDateTime(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FXTradingApp();
});