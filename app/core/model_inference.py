"""
Real Model Inference for Trading Signals
Chỉ sử dụng real model - No mock data
"""

import pandas as pd
import numpy as np
import joblib
import os
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class RealModelInference:
    """Real-only model inference cho trading signals"""
    
    def __init__(self, model_path: str = None, scaler_path: str = None):
        """
        Initialize real model inference
        
        Args:
            model_path: Path to trained model file
            scaler_path: Path to feature scaler file
        """
        self.model = None
        self.scaler = None
        self.model_path = model_path or self._find_model_path()
        self.scaler_path = scaler_path or self._find_scaler_path()
        
        # Define confidence levels
        self.confidence_levels = [0.4, 0.5, 0.6, 0.7, 0.8]
        
        # Load model và scaler
        self._load_model_and_scaler()
        
    def _find_model_path(self) -> str:
        """Tìm model file trong project"""
        possible_paths = [
            'models/model15/xgboost_model.pkl',
            'app/models/model15/xgboost_model.pkl',
            '../models/model15/xgboost_model.pkl',
            '/media/duongn/New Volume/UIT/AI Challenge/DATA DSTCDSTC/stock-quant/models/model15/xgboost_model.pkl'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found model at: {path}")
                return path
                
        raise FileNotFoundError("❌ No model found. Please ensure model exists.")
        
    def _find_scaler_path(self) -> str:
        """Tìm scaler file trong project"""
        possible_paths = [
            'models/model15/feature_scaler.pkl',
            'app/models/model15/feature_scaler.pkl',
            '../models/model15/feature_scaler.pkl',
            '/media/duongn/New Volume/UIT/AI Challenge/DATA DSTCDSTC/stock-quant/models/model15/feature_scaler.pkl'
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                logger.info(f"✅ Found scaler at: {path}")
                return path
                
        logger.warning("⚠️ No scaler found, will proceed without scaling")
        return None
        
    def _load_model_and_scaler(self):
        """Load trained model và scaler"""
        try:
            # Load model
            if self.model_path and os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info(f"✅ Loaded real model from: {self.model_path}")
            else:
                raise FileNotFoundError("Model file not found")
                
            # Load scaler
            if self.scaler_path and os.path.exists(self.scaler_path):
                self.scaler = joblib.load(self.scaler_path)
                logger.info(f"✅ Loaded scaler from: {self.scaler_path}")
            else:
                logger.warning("⚠️ No scaler available")
                self.scaler = None
                
        except Exception as e:
            logger.error(f"❌ Error loading model/scaler: {e}")
            raise RuntimeError(f"Cannot load model: {e}")
            
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for prediction - match backtest engine exactly"""
        # Match exactly with backtest engine exclude list
        exclude_cols = [
            'ticker', 'timestamp', 'label', 'hit_time', 'hit_type',
            'ub', 'lb', 'vbar_end'
        ]
        
        feature_cols = [col for col in data.columns if col not in exclude_cols]
        X = data[feature_cols].copy()
        
        # Handle missing values like backtest engine
        X_clean = X.fillna(X.median()) 
        X_clean = X_clean.replace([np.inf, -np.inf], np.nan)
        X_clean = X_clean.fillna(X_clean.median())
        
        # Scale features
        X_scaled = self.scaler.transform(X_clean)
        
        return pd.DataFrame(X_scaled, columns=feature_cols, index=data.index)
            
    def predict_with_confidence(self, 
                               features: pd.DataFrame, 
                               tickers: List[str] = None) -> Dict[str, Dict]:
        """
        Predict signals với multiple confidence levels
        
        Args:
            features: DataFrame với features
            tickers: List tickers tương ứng
            
        Returns:
            Dict: Results cho từng confidence level
        """
        if self.model is None:
            raise RuntimeError("No model available for prediction")
            
        if tickers is None:
            tickers = [f"TICKER_{i}" for i in range(len(features))]
            
        results = {}
        
        # Get model predictions
        try:
            predictions = self.model.predict(features)
            probabilities = self.model.predict_proba(features)
            
            # Calculate confidence (max probability)
            confidence_scores = np.max(probabilities, axis=1)
            
            # Convert predictions to signals (similar to backtest engine)
            label_map = {0: -1, 1: 0, 2: 1}  # 0: SELL, 1: HOLD, 2: BUY
            signals = np.vectorize(label_map.get)(predictions)
            
            # Process each confidence level
            for confidence_threshold in self.confidence_levels:
                level_signals = self._apply_confidence_threshold(
                    signals, confidence_scores, probabilities, 
                    tickers, confidence_threshold
                )
                
                results[f"conf_{confidence_threshold}"] = {
                    'confidence_threshold': confidence_threshold,
                    'signals': level_signals,
                    'summary': self._calculate_summary(level_signals)
                }
                
        except Exception as e:
            logger.error(f"❌ Prediction error: {e}")
            # Return empty results
            for confidence_threshold in self.confidence_levels:
                results[f"conf_{confidence_threshold}"] = {
                    'confidence_threshold': confidence_threshold,
                    'signals': [],
                    'summary': self._empty_summary()
                }
        
        logger.info(f"📊 Generated predictions for {len(self.confidence_levels)} confidence levels")
        return results
        
    def _apply_confidence_threshold(self, 
                                   signals: np.ndarray,
                                   confidence_scores: np.ndarray,
                                   probabilities: np.ndarray,
                                   tickers: List[str],
                                   confidence_threshold: float) -> List[Dict]:
        """Apply confidence threshold to signals"""
        level_signals = []
        
        for i, ticker in enumerate(tickers):
            original_signal = signals[i]
            confidence = confidence_scores[i]
            
            # Apply confidence threshold
            if confidence >= confidence_threshold:
                action = self._signal_to_action(original_signal)
            else:
                action = "HOLD"  # Low confidence → HOLD
                original_signal = 0
                
            level_signals.append({
                'ticker': ticker,
                'action': action,
                'confidence': float(confidence),
                'signal_class': int(original_signal),
                'probabilities': probabilities[i].tolist() if i < len(probabilities) else [0, 0, 0],
                'meets_threshold': confidence >= confidence_threshold
            })
            
        return level_signals
        
    def _signal_to_action(self, signal: int) -> str:
        """Convert signal to action string"""
        mapping = {-1: "SELL", 0: "HOLD", 1: "BUY"}
        return mapping.get(signal, "HOLD")
        
    def _calculate_summary(self, signals: List[Dict]) -> Dict:
        """Tính summary statistics cho signals"""
        total_signals = len(signals)
        buy_signals = len([s for s in signals if s['action'] == 'BUY'])
        sell_signals = len([s for s in signals if s['action'] == 'SELL'])
        hold_signals = len([s for s in signals if s['action'] == 'HOLD'])
        
        active_signals = buy_signals + sell_signals
        
        # Calculate average confidence for signals that meet threshold
        meeting_threshold = [s for s in signals if s['meets_threshold']]
        avg_confidence = np.mean([s['confidence'] for s in meeting_threshold]) if meeting_threshold else 0.0
        
        return {
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'active_signals': active_signals,
            'active_rate': active_signals / total_signals if total_signals > 0 else 0,
            'avg_confidence': float(avg_confidence)
        }
        
    def _empty_summary(self) -> Dict:
        """Empty summary when no predictions"""
        return {
            'total_signals': 0,
            'buy_signals': 0,
            'sell_signals': 0,
            'hold_signals': 0,
            'active_signals': 0,
            'active_rate': 0.0,
            'avg_confidence': 0.0
        }
        
    def format_signals_for_display(self, results: Dict[str, Dict]) -> Dict:
        """Format signals để hiển thị trên dashboard"""
        formatted = {}
        
        for level, data in results.items():
            confidence = data['confidence_threshold']
            signals = data['signals']
            summary = data['summary']
            
            # Chỉ lấy active signals
            active_signals = [s for s in signals if s['action'] != 'HOLD']
            
            formatted[level] = {
                'name': f"Confidence {confidence*100:.0f}%",
                'confidence_threshold': confidence,
                'total_tickers': len(signals),
                'active_signals': len(active_signals),
                'buy_count': summary['buy_signals'],
                'sell_count': summary['sell_signals'],
                'avg_confidence': summary['avg_confidence'],
                'active_rate': summary['active_rate'],
                'signals': active_signals[:10],  # Top 10 for display
                'color': self._get_color_for_confidence(confidence)
            }
            
        return formatted
        
    def _get_color_for_confidence(self, confidence: float) -> str:
        """Get color code cho confidence level"""
        if confidence >= 0.7:
            return "#e74c3c"  # Red - High confidence
        elif confidence >= 0.6:
            return "#f39c12"  # Orange - Medium-high confidence  
        elif confidence >= 0.5:
            return "#f1c40f"  # Yellow - Medium confidence
        else:
            return "#3498db"  # Blue - Low confidence
            
    def get_status(self) -> Dict:
        """Get status của model"""
        return {
            'model_loaded': self.model is not None,
            'model_path': self.model_path,
            'model_type': type(self.model).__name__ if self.model else "None",
            'scaler_available': self.scaler is not None,
            'scaler_path': self.scaler_path,
            'confidence_levels': self.confidence_levels,
        } 