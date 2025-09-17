/**
 * WebSocket client for real-time trading signals dashboard
 */

class DashboardWebSocket {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.heartbeatInterval = null;
        this.isConnected = false;
        this.messageHandlers = {};
        
        this.setupEventHandlers();
        this.connect();
    }
    
    connect() {
        try {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws/signals`;
            
            this.ws = new WebSocket(wsUrl);
            this.setupWebSocketHandlers();
            
            console.log('🔌 Attempting WebSocket connection...');
        } catch (error) {
            console.error('❌ WebSocket connection failed:', error);
            this.handleReconnect();
        }
    }
    
    setupWebSocketHandlers() {
        this.ws.onopen = (event) => {
            console.log('✅ WebSocket connected');
            this.isConnected = true;
            this.reconnectAttempts = 0;
            this.reconnectDelay = 1000;
            
            this.updateConnectionStatus(true);
            this.startHeartbeat();
            
            // Send initial ping
            this.send({ type: 'ping' });
        };
        
        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleMessage(data);
            } catch (error) {
                console.error('❌ Error parsing WebSocket message:', error);
            }
        };
        
        this.ws.onclose = (event) => {
            console.log('🔌 WebSocket disconnected:', event.code, event.reason);
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.stopHeartbeat();
            
            if (event.code !== 1000) { // Not a normal closure
                this.handleReconnect();
            }
        };
        
        this.ws.onerror = (error) => {
            console.error('❌ WebSocket error:', error);
            this.isConnected = false;
            this.updateConnectionStatus(false);
        };
    }
    
    setupEventHandlers() {
        // Register message handlers for different message types
        this.onMessage('initial_data', (data) => {
            console.log('📊 Received initial data');
            this.updateDashboard(data);
        });
        
        this.onMessage('signals_update', (data) => {
            console.log('🎯 Received signals update');
            this.updateSignals(data);
        });
        
        this.onMessage('market_update', (data) => {
            console.log('📈 Received market update');
            this.updateMarketData(data);
        });
        
        this.onMessage('portfolio_update', (data) => {
            console.log('💼 Received portfolio update');
            this.updatePortfolio(data);
        });
        
        this.onMessage('heartbeat', (data) => {
            // Silent heartbeat response
            this.send({ type: 'pong' });
        });
        
        this.onMessage('pong', (data) => {
            // Heartbeat acknowledged
        });
    }
    
    handleMessage(message) {
        const { type, data } = message;
        
        if (this.messageHandlers[type]) {
            this.messageHandlers[type](data);
        } else {
            console.warn('🤷 Unknown message type:', type);
        }
    }
    
    onMessage(type, handler) {
        this.messageHandlers[type] = handler;
    }
    
    send(message) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(message));
            return true;
        } else {
            console.warn('⚠️ WebSocket not connected, message not sent');
            return false;
        }
    }
    
    handleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Max reconnection attempts reached');
            this.updateConnectionStatus(false, 'Connection failed');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`🔄 Reconnecting in ${this.reconnectDelay}ms (attempt ${this.reconnectAttempts})`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay);
        
        // Exponential backoff with jitter
        this.reconnectDelay = Math.min(this.reconnectDelay * 2 + Math.random() * 1000, 30000);
    }
    
    startHeartbeat() {
        this.heartbeatInterval = setInterval(() => {
            if (this.isConnected) {
                this.send({ type: 'ping' });
            }
        }, 30000); // 30 seconds
    }
    
    stopHeartbeat() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
        }
    }
    
    updateConnectionStatus(isConnected, message = '') {
        const statusElement = document.getElementById('connection-status');
        if (statusElement) {
            const icon = statusElement.querySelector('i');
            const text = statusElement.querySelector('span');
            
            if (isConnected) {
                icon.className = 'fas fa-wifi';
                icon.style.color = 'var(--green)';
                text.textContent = 'Connected';
                statusElement.style.color = 'var(--green)';
            } else {
                icon.className = 'fas fa-wifi';
                icon.style.color = 'var(--red)';
                text.textContent = message || 'Disconnected';
                statusElement.style.color = 'var(--red)';
            }
        }
    }
    
    updateDashboard(data) {
        if (data.market_status) {
            this.updateMarketData(data.market_status);
        }
        if (data.strategy_performance) {
            this.updateStrategyPerformance(data.strategy_performance);
        }
        if (data.portfolio_summary) {
            this.updatePortfolio(data.portfolio_summary);
        }
    }
    
    updateSignals(data) {
        if (data.signals) {
            this.addNewSignals(data.signals);
        }
        if (data.portfolio) {
            this.updatePortfolio(data.portfolio);
        }
        if (data.market_data) {
            this.updateMarketData(data.market_data);
        }
    }
    
    updateMarketData(data) {
        // Update VN-Index
        const vnindexValue = document.getElementById('vnindex-value');
        const vnindexChange = document.getElementById('vnindex-change');
        
        if (vnindexValue && data.vnindex) {
            vnindexValue.textContent = data.vnindex.value;
        }
        if (vnindexChange && data.vnindex) {
            vnindexChange.textContent = `${data.vnindex.change > 0 ? '+' : ''}${data.vnindex.change}%`;
            vnindexChange.className = `index-change ${data.vnindex.change >= 0 ? 'positive' : 'negative'}`;
        }
        
        // Update VN30
        const vn30Value = document.getElementById('vn30-value');
        const vn30Change = document.getElementById('vn30-change');
        
        if (vn30Value && data.vn30) {
            vn30Value.textContent = data.vn30.value;
        }
        if (vn30Change && data.vn30) {
            vn30Change.textContent = `${data.vn30.change > 0 ? '+' : ''}${data.vn30.change}%`;
            vn30Change.className = `index-change ${data.vn30.change >= 0 ? 'positive' : 'negative'}`;
        }
        
        // Update active tickers
        const activeTickers = document.getElementById('active-tickers');
        if (activeTickers && data.active_tickers !== undefined) {
            activeTickers.textContent = `${data.active_tickers}/9`;
        }
        
        // Update last update time
        const lastUpdate = document.getElementById('last-update');
        if (lastUpdate) {
            lastUpdate.textContent = new Date().toLocaleTimeString();
        }
    }
    
    addNewSignals(signals) {
        const signalsContainer = document.getElementById('signals-container');
        if (!signalsContainer) return;
        
        // Add new signals to the top
        signals.forEach(signal => {
            const signalElement = this.createSignalElement(signal);
            signalsContainer.insertBefore(signalElement, signalsContainer.firstChild);
        });
        
        // Remove old signals (keep max 50)
        const signalItems = signalsContainer.querySelectorAll('.signal-item');
        if (signalItems.length > 50) {
            for (let i = 50; i < signalItems.length; i++) {
                signalItems[i].remove();
            }
        }
        
        this.updateSignalsSummary();
    }
    
    createSignalElement(signal) {
        const div = document.createElement('div');
        div.className = `signal-item ${signal.action.toLowerCase()}`;
        
        const actionIcon = signal.action === 'BUY' ? '↑' : signal.action === 'SELL' ? '↓' : '−';
        const actionClass = signal.action.toLowerCase();
        
        div.innerHTML = `
            <div class="signal-time">${new Date(signal.timestamp).toLocaleTimeString()}</div>
            <div class="signal-ticker">${signal.ticker}</div>
            <div class="signal-action ${actionClass}">
                <i class="fas fa-arrow-${signal.action === 'BUY' ? 'up' : signal.action === 'SELL' ? 'down' : 'minus'}"></i>
                ${signal.action}
            </div>
            <div class="signal-confidence">${(signal.confidence * 100).toFixed(1)}%</div>
            <div class="signal-strategy">${signal.strategy_name}</div>
        `;
        
        return div;
    }
    
    updateSignalsSummary() {
        const signalItems = document.querySelectorAll('.signal-item');
        const totalSignals = signalItems.length;
        
        // Count profitable signals (this would need backend data)
        const profitable = Math.floor(totalSignals * 0.67); // Example
        const winRate = totalSignals > 0 ? (profitable / totalSignals * 100) : 0;
        
        // Update summary
        const signalsToday = document.getElementById('signals-today');
        const profitableSignals = document.getElementById('profitable-signals');
        const winRateElement = document.getElementById('win-rate');
        
        if (signalsToday) signalsToday.textContent = totalSignals;
        if (profitableSignals) profitableSignals.textContent = profitable;
        if (winRateElement) winRateElement.textContent = `${winRate.toFixed(1)}%`;
    }
    
    updatePortfolio(data) {
        // Update total P&L
        const totalPnL = document.getElementById('total-pnl');
        if (totalPnL && data.total_pnl !== undefined) {
            totalPnL.textContent = `${data.total_pnl > 0 ? '+' : ''}${data.total_pnl.toFixed(2)}%`;
            totalPnL.className = `value-amount ${data.total_pnl >= 0 ? 'positive' : 'negative'}`;
        }
        
        // Update daily P&L
        const dailyPnL = document.getElementById('daily-pnl');
        if (dailyPnL && data.daily_pnl !== undefined) {
            dailyPnL.textContent = `${data.daily_pnl > 0 ? '+' : ''}${data.daily_pnl.toFixed(2)}%`;
            dailyPnL.className = `metric-value ${data.daily_pnl >= 0 ? 'positive' : 'negative'}`;
        }
        
        // Update other metrics
        const maxDrawdown = document.getElementById('max-drawdown');
        if (maxDrawdown && data.max_drawdown !== undefined) {
            maxDrawdown.textContent = `${data.max_drawdown.toFixed(2)}%`;
        }
        
        const sharpeRatio = document.getElementById('sharpe-ratio');
        if (sharpeRatio && data.sharpe_ratio !== undefined) {
            sharpeRatio.textContent = data.sharpe_ratio.toFixed(2);
        }
        
        const activePositions = document.getElementById('active-positions');
        if (activePositions && data.active_positions !== undefined) {
            activePositions.textContent = `${data.active_positions}/15`;
        }
    }
    
    updateStrategyPerformance(data) {
        // This would update the strategy cards
        // Implementation depends on the data structure
        console.log('📊 Strategy performance update:', data);
    }
    
    close() {
        this.stopHeartbeat();
        if (this.ws) {
            this.ws.close(1000, 'Dashboard closed');
        }
    }
}

// Global WebSocket instance
let dashboardWS = null;

// Initialize WebSocket when DOM is loaded
function initializeWebSocket() {
    if (!dashboardWS) {
        dashboardWS = new DashboardWebSocket();
    }
}

// Clean up WebSocket on page unload
window.addEventListener('beforeunload', () => {
    if (dashboardWS) {
        dashboardWS.close();
    }
}); 