/**
 * Dashboard JavaScript functions
 */

// Global variables
let dashboard = null;

// Dashboard initialization
function initializeDashboard() {
    console.log('🚀 Initializing dashboard...');
    
    // Initialize WebSocket
    initializeWebSocket();
    
    // Setup event listeners
    setupEventListeners();
    
    // Start periodic updates
    startPeriodicUpdates();
    
    console.log('✅ Dashboard initialized');
}

function setupEventListeners() {
    // Strategy filter
    const strategyFilter = document.getElementById('strategy-filter');
    if (strategyFilter) {
        strategyFilter.addEventListener('change', filterSignals);
    }
    
    // Ticker selector for chart
    const tickerSelect = document.getElementById('ticker-select');
    if (tickerSelect) {
        tickerSelect.addEventListener('change', updateChart);
    }
    
    // Refresh button
    const refreshButtons = document.querySelectorAll('.btn-refresh');
    refreshButtons.forEach(button => {
        button.addEventListener('click', refreshMarketData);
    });
}

function startPeriodicUpdates() {
    // Update time every second
    setInterval(updateCurrentTime, 1000);
    
    // Update charts every 30 seconds
    setInterval(updateCharts, 30000);
}

function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        timeElement.textContent = new Date().toLocaleTimeString();
    }
}

function filterSignals() {
    const filter = document.getElementById('strategy-filter').value;
    const signalItems = document.querySelectorAll('.signal-item');
    
    signalItems.forEach(item => {
        const strategy = item.querySelector('.signal-strategy').textContent;
        
        if (filter === 'all' || strategy.includes(filter)) {
            item.style.display = 'grid';
        } else {
            item.style.display = 'none';
        }
    });
}

async function refreshMarketData() {
    console.log('🔄 Refreshing market data...');
    
    try {
        const response = await fetch('/api/market/status');
        const data = await response.json();
        
        if (data.market_status) {
            updateMarketDisplay(data.market_status);
        }
        
        // Show success feedback
        showNotification('Market data refreshed', 'success');
        
    } catch (error) {
        console.error('❌ Error refreshing market data:', error);
        showNotification('Failed to refresh market data', 'error');
    }
}

function updateMarketDisplay(marketData) {
    // Update VN-Index
    const vnindexValue = document.getElementById('vnindex-value');
    const vnindexChange = document.getElementById('vnindex-change');
    
    if (vnindexValue && marketData.vnindex) {
        vnindexValue.textContent = marketData.vnindex.value;
    }
    if (vnindexChange && marketData.vnindex) {
        const change = marketData.vnindex.change;
        vnindexChange.textContent = `${change > 0 ? '+' : ''}${change}%`;
        vnindexChange.className = `index-change ${change >= 0 ? 'positive' : 'negative'}`;
    }
    
    // Update VN30
    const vn30Value = document.getElementById('vn30-value');
    const vn30Change = document.getElementById('vn30-change');
    
    if (vn30Value && marketData.vn30) {
        vn30Value.textContent = marketData.vn30.value;
    }
    if (vn30Change && marketData.vn30) {
        const change = marketData.vn30.change;
        vn30Change.textContent = `${change > 0 ? '+' : ''}${change}%`;
        vn30Change.className = `index-change ${change >= 0 ? 'positive' : 'negative'}`;
    }
    
    // Update last update time
    const lastUpdate = document.getElementById('last-update');
    if (lastUpdate) {
        lastUpdate.textContent = new Date().toLocaleTimeString();
    }
}

function updateChart() {
    const selectedTicker = document.getElementById('ticker-select').value;
    console.log(`📊 Updating chart for ${selectedTicker}`);
    
    // This would integrate with Chart.js or similar library
    // For now, just log the action
    showNotification(`Chart updated for ${selectedTicker}`, 'info');
}

function updateCharts() {
    // Update all charts with latest data
    console.log('📊 Updating all charts...');
    
    // This would update price charts, performance charts, etc.
    // Implementation depends on charting library used
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="closeNotification(this)">×</button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

function closeNotification(button) {
    const notification = button.closest('.notification');
    if (notification && notification.parentNode) {
        notification.parentNode.removeChild(notification);
    }
}

// Loading overlay functions
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('show');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('show');
    }
}

// Strategy card interactions
function toggleStrategyDetails(strategyId) {
    const card = document.querySelector(`[data-strategy="${strategyId}"]`);
    if (card) {
        card.classList.toggle('expanded');
    }
}

// Portfolio switching (for multi-account demo)
async function switchPortfolio(accountId) {
    console.log(`💼 Switching to portfolio: ${accountId}`);
    
    try {
        showLoading();
        
        const response = await fetch(`/api/portfolio/performance?account=${accountId}`);
        const data = await response.json();
        
        if (data.performance) {
            updatePortfolioDisplay(data.performance);
            showNotification(`Switched to ${accountId} portfolio`, 'success');
        }
        
    } catch (error) {
        console.error('❌ Error switching portfolio:', error);
        showNotification('Failed to switch portfolio', 'error');
    } finally {
        hideLoading();
    }
}

function updatePortfolioDisplay(portfolioData) {
    // Update portfolio metrics
    const totalPnL = document.getElementById('total-pnl');
    if (totalPnL && portfolioData.total_pnl !== undefined) {
        totalPnL.textContent = `${portfolioData.total_pnl > 0 ? '+' : ''}${portfolioData.total_pnl.toFixed(2)}%`;
        totalPnL.className = `value-amount ${portfolioData.total_pnl >= 0 ? 'positive' : 'negative'}`;
    }
    
    // Update other metrics...
}

// Risk monitoring functions
function updateRiskGauge(exposure) {
    const gauge = document.getElementById('exposure-gauge');
    if (!gauge) return;
    
    const value = gauge.querySelector('.gauge-value');
    const status = gauge.querySelector('.gauge-status');
    
    if (value) {
        value.textContent = `${(exposure * 100).toFixed(1)}%`;
    }
    
    if (status) {
        let statusText = 'Safe';
        let statusClass = 'safe';
        
        if (exposure > 0.9) {
            statusText = 'High';
            statusClass = 'danger';
        } else if (exposure > 0.8) {
            statusText = 'Moderate';
            statusClass = 'warning';
        }
        
        status.textContent = statusText;
        status.className = `gauge-status ${statusClass}`;
    }
}

// API helper functions
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
        
    } catch (error) {
        console.error(`❌ API call failed: ${endpoint}`, error);
        throw error;
    }
}

// Utility functions
function formatPrice(price) {
    return new Intl.NumberFormat('vi-VN').format(price);
}

function formatPercent(value, decimals = 2) {
    return `${value > 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('vi-VN');
}

function formatDateTime(timestamp) {
    return new Date(timestamp).toLocaleString('vi-VN');
}

// Export functions for global use
window.dashboard = {
    initialize: initializeDashboard,
    refreshMarketData,
    updateChart,
    showNotification,
    switchPortfolio,
    updateRiskGauge,
    formatPrice,
    formatPercent,
    formatTime,
    formatDateTime
}; 