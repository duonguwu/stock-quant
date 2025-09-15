# Kế hoạch triển khai Modules từ Notebooks

## Tổng quan

Chuyển đổi code từ Jupyter notebooks thành Python modules có thể tích hợp vào hệ thống chính.

## 1. Stock Screening Module

### 1.1 Cấu trúc module
```
src/
├── screening/
│   ├── __init__.py
│   ├── fundamental_screener.py    # Core screening logic
│   ├── style_classifier.py        # Growth vs Defensive classification
│   └── config/
│       └── screening_config.yaml  # Screening parameters
```

### 1.2 Chức năng chính

#### `fundamental_screener.py`
```python
class FundamentalScreener:
    """Fundamental stock screening với multi-year support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.screening_rules = self._load_screening_rules()
    
    def calculate_eps_change(self, df_current: pd.DataFrame, 
                           df_previous: pd.DataFrame) -> pd.DataFrame:
        """Tính EPS change giữa năm hiện tại và năm trước"""
        pass
    
    def screen_stocks(self, df_current: pd.DataFrame, 
                     df_previous: pd.DataFrame = None, 
                     year: int = None) -> pd.DataFrame:
        """Lọc cổ phiếu theo tiêu chí fundamental"""
        pass
    
    def screen_multiple_years(self, dataframes_dict: Dict[int, pd.DataFrame]) -> Dict[int, pd.DataFrame]:
        """Lọc cổ phiếu cho nhiều năm"""
        pass
```

#### `style_classifier.py`
```python
class StyleClassifier:
    """Phân loại cổ phiếu theo investment style"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.defensive_sectors = config.get('defensive_sectors', [])
    
    def calculate_growth_score(self, df: pd.DataFrame) -> pd.Series:
        """Tính điểm growth dựa trên EPS growth, ROE, market cap"""
        pass
    
    def calculate_defensive_score(self, df: pd.DataFrame) -> pd.Series:
        """Tính điểm defensive dựa trên sector, PE, PB, market cap"""
        pass
    
    def select_top_stocks(self, df_screened: pd.DataFrame, 
                         n_growth: int = 3, n_defensive: int = 2) -> pd.DataFrame:
        """Chọn top stocks theo style"""
        pass
```

### 1.3 Configuration
```yaml
# config/screening_config.yaml
screening:
  # Fundamental filters
  market_cap_min: 1000000000  # 1B VND
  eps_growth_min: 0.0
  pe_max_ratio: 1.0  # vs sector average
  pb_min: 1.0
  pb_max: 2.0
  roe_min: 0.15
  volume_min: 100000
  
  # Style classification
  defensive_sectors:
    - "Điện, nước & xăng dầu khí đốt"
    - "Thực phẩm và đồ uống"
    - "Bảo hiểm"
  
  # Scoring weights
  growth_weights:
    eps_growth: 0.55
    roe: 0.35
    market_cap: 0.10
  
  defensive_weights:
    sector: 0.35
    market_cap: 0.30
    pe: 0.20
    pb_proximity: 0.15
```

## 2. Rule-based Trading Module

### 2.1 Cấu trúc module
```
src/
├── trading/
│   ├── __init__.py
│   ├── vsa_patterns.py          # VSA/Wyckoff pattern detection
│   ├── signal_generator.py      # Signal generation logic
│   ├── portfolio_optimizer.py   # Portfolio optimization
│   ├── rule_backtester.py       # Rule-based backtesting
│   └── config/
│       └── trading_config.yaml  # Trading parameters
```

### 2.2 Chức năng chính

#### `vsa_patterns.py`
```python
class VSAPatternDetector:
    """Volume Spread Analysis pattern detection"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vol_thresholds = config.get('volume_thresholds', {})
        self.spread_thresholds = config.get('spread_thresholds', {})
    
    def detect_bar_type(self, df: pd.DataFrame) -> pd.Series:
        """Phân loại bar: up, down, flat"""
        pass
    
    def detect_volume_type(self, df: pd.DataFrame) -> pd.Series:
        """Phân loại volume: low, medium, high"""
        pass
    
    def detect_spread_type(self, df: pd.DataFrame) -> pd.Series:
        """Phân loại spread: low, medium, high"""
        pass
    
    def detect_close_position(self, df: pd.DataFrame) -> pd.Series:
        """Phân loại vị trí close: bottom, middle, top third"""
        pass
    
    def detect_sos_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect Signs of Strength patterns"""
        pass
    
    def detect_sow_patterns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Detect Signs of Weakness patterns"""
        pass
```

#### `signal_generator.py`
```python
class RuleBasedSignalGenerator:
    """Generate trading signals từ VSA patterns + RSI"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.vsa_detector = VSAPatternDetector(config)
        self.rsi_params = config.get('rsi', {})
        self.signal_params = config.get('signal', {})
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate buy/sell signals với state machine logic"""
        pass
    
    def _apply_state_machine(self, df: pd.DataFrame) -> pd.Series:
        """Apply state machine: first BUY required, T+2 constraint"""
        pass
```

#### `portfolio_optimizer.py`
```python
class PortfolioOptimizer:
    """Portfolio optimization using quadratic programming"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.optimization_params = config.get('optimization', {})
    
    def optimize_weights(self, df: pd.DataFrame, tickers: List[str]) -> Tuple[pd.DataFrame, Dict]:
        """Optimize portfolio weights với constraints"""
        pass
    
    def _setup_optimization_problem(self, returns: pd.DataFrame, 
                                  constraints: Dict) -> cp.Problem:
        """Setup quadratic programming problem"""
        pass
```

#### `rule_backtester.py`
```python
class RuleBasedBacktester:
    """Backtesting cho rule-based system"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.commission = config.get('commission', 0.001)
        self.board_lot = config.get('board_lot', 100)
    
    def backtest_single_stock(self, df: pd.DataFrame, ticker: str, 
                            cash: float) -> Dict:
        """Backtest single stock với signals"""
        pass
    
    def backtest_portfolio(self, df: pd.DataFrame, weights_df: pd.DataFrame,
                         capital: float) -> Tuple[Dict, pd.DataFrame, pd.DataFrame]:
        """Backtest portfolio với optimized weights"""
        pass
    
    def compare_with_benchmark(self, portfolio_curve: pd.DataFrame,
                             benchmark_ticker: str = "VNINDEX") -> Dict:
        """So sánh với benchmark"""
        pass
```

### 2.3 Configuration
```yaml
# config/trading_config.yaml
trading:
  # VSA parameters
  volume_thresholds:
    low: 0.85
    high: 1.2
  
  spread_thresholds:
    low: 0.8
    high: 1.2
    lookback: 20
  
  # Signal generation
  signal:
    min_true: 1
    tplus2_bars: 2
  
  rsi:
    buy_threshold: 35
    sell_threshold: 65
    period: 14
  
  # Portfolio optimization
  optimization:
    capital: 1000000000  # 1B VND
    lookback_days: 180
    target_return_range: [0.20, 0.25]
    bank_rate: 0.10
    weight_lower: 0.05
    weight_upper: 0.50
  
  # Backtesting
  backtesting:
    commission: 0.001
    board_lot: 100
    benchmark: "VNINDEX"
```

## 3. Integration với Main System

### 3.1 Cập nhật main.py
```python
# main.py
from src.screening.fundamental_screener import FundamentalScreener
from src.screening.style_classifier import StyleClassifier
from src.trading.signal_generator import RuleBasedSignalGenerator
from src.trading.portfolio_optimizer import PortfolioOptimizer
from src.trading.rule_backtester import RuleBasedBacktester

def run_ml_pipeline():
    """Chạy ML-based pipeline (existing)"""
    pass

def run_rule_based_pipeline():
    """Chạy rule-based pipeline (new)"""
    # 1. Stock screening
    screener = FundamentalScreener(config['screening'])
    screened_stocks = screener.screen_multiple_years(dataframes_dict)
    
    # 2. Style classification
    classifier = StyleClassifier(config['screening'])
    top_stocks = {}
    for year, df in screened_stocks.items():
        top_stocks[year] = classifier.select_top_stocks(df)
    
    # 3. Rule-based trading
    signal_generator = RuleBasedSignalGenerator(config['trading'])
    optimizer = PortfolioOptimizer(config['trading'])
    backtester = RuleBasedBacktester(config['trading'])
    
    # 4. Run analysis for each year
    results = {}
    for year, stocks_df in top_stocks.items():
        # Generate signals
        signals_df = signal_generator.generate_signals(data_df)
        
        # Optimize portfolio
        weights_df, portfolio_info = optimizer.optimize_weights(signals_df, tickers)
        
        # Backtest
        summary, per_ticker_stats, portfolio_curve = backtester.backtest_portfolio(
            signals_df, weights_df, capital
        )
        
        results[year] = {
            'weights': weights_df,
            'portfolio_info': portfolio_info,
            'backtest_summary': summary,
            'per_ticker_stats': per_ticker_stats,
            'portfolio_curve': portfolio_curve
        }
    
    return results

def main():
    """Main entry point với option chọn system"""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--system', choices=['ml', 'rule', 'both'], default='both')
    args = parser.parse_args()
    
    if args.system in ['ml', 'both']:
        ml_results = run_ml_pipeline()
    
    if args.system in ['rule', 'both']:
        rule_results = run_rule_based_pipeline()
    
    if args.system == 'both':
        # Compare results
        compare_systems(ml_results, rule_results)
```

### 3.2 Cập nhật config system
```python
# src/utils/config_loader.py
def load_all_configs() -> Dict[str, Any]:
    """Load tất cả configs"""
    configs = {}
    
    # Existing configs
    configs['data'] = load_config('config/data_config.yaml')
    configs['labeling'] = load_config('config/labeling_config.yaml')
    configs['model'] = load_config('config/model_config.yaml')
    
    # New configs
    configs['screening'] = load_config('config/screening_config.yaml')
    configs['trading'] = load_config('config/trading_config.yaml')
    
    return configs
```

## 4. Implementation Timeline

### Phase 1: Core Modules (Week 1-2)
- [ ] Tạo cấu trúc thư mục mới
- [ ] Implement `FundamentalScreener`
- [ ] Implement `StyleClassifier`
- [ ] Tạo screening config
- [ ] Unit tests cho screening

### Phase 2: Trading Modules (Week 3-4)
- [ ] Implement `VSAPatternDetector`
- [ ] Implement `RuleBasedSignalGenerator`
- [ ] Implement `PortfolioOptimizer`
- [ ] Implement `RuleBasedBacktester`
- [ ] Tạo trading config
- [ ] Unit tests cho trading

### Phase 3: Integration (Week 5)
- [ ] Cập nhật main.py
- [ ] Cập nhật config loader
- [ ] Integration tests
- [ ] Documentation
- [ ] Performance testing

### Phase 4: Advanced Features (Week 6+)
- [ ] Hybrid system (ML + Rule-based)
- [ ] Real-time data integration
- [ ] Advanced risk management
- [ ] Web dashboard

## 5. Testing Strategy

### 5.1 Unit Tests
```python
# tests/test_screening.py
def test_eps_change_calculation():
    """Test EPS change calculation"""
    pass

def test_market_cap_filter():
    """Test market cap filtering"""
    pass

def test_style_classification():
    """Test growth vs defensive classification"""
    pass

# tests/test_trading.py
def test_vsa_pattern_detection():
    """Test VSA pattern detection"""
    pass

def test_signal_generation():
    """Test signal generation logic"""
    pass

def test_portfolio_optimization():
    """Test portfolio optimization"""
    pass
```

### 5.2 Integration Tests
```python
# tests/test_integration.py
def test_end_to_end_screening():
    """Test complete screening pipeline"""
    pass

def test_end_to_end_trading():
    """Test complete trading pipeline"""
    pass

def test_performance_comparison():
    """Test ML vs Rule-based performance"""
    pass
```

## 6. Migration Strategy

### 6.1 Data Migration
- [ ] Convert notebook data files thành structured format
- [ ] Tạo data validation scripts
- [ ] Backup existing data

### 6.2 Code Migration
- [ ] Extract functions từ notebooks
- [ ] Refactor thành classes
- [ ] Add error handling
- [ ] Add logging

### 6.3 Configuration Migration
- [ ] Convert hardcoded parameters thành config files
- [ ] Tạo config validation
- [ ] Document all parameters

## 7. Benefits của Module Approach

### 7.1 Maintainability
- **Modular**: Dễ maintain và debug
- **Reusable**: Có thể sử dụng lại components
- **Testable**: Dễ viết unit tests
- **Configurable**: Parameters externalized

### 7.2 Scalability
- **Extensible**: Dễ thêm features mới
- **Parallelizable**: Có thể chạy parallel
- **Distributable**: Có thể deploy trên multiple machines

### 7.3 Production Ready
- **Error Handling**: Proper exception handling
- **Logging**: Comprehensive logging
- **Monitoring**: Performance monitoring
- **Documentation**: API documentation

## 8. Kết luận

Việc chuyển đổi từ notebooks thành modules sẽ:

1. **Tăng tính chuyên nghiệp** của codebase
2. **Dễ maintain và extend** trong tương lai
3. **Tích hợp tốt hơn** với ML pipeline hiện tại
4. **Chuẩn bị cho production** deployment
5. **Tạo foundation** cho hybrid system

**Recommendation**: Bắt đầu với Phase 1 (Screening modules) trước vì đây là foundation cho cả 2 trading systems.
