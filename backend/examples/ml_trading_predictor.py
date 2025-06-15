"""
Enkel integration för att demonstrera predict_proba användning i trading-kontext.
Denna fil kan användas som referens för att integrera ML-modeller i strategierna.
"""
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np


class TradingMLPredictor:
    """
    Enkel ML-baserad trading predictor som använder predict_proba för 
    att generera signaler med konfidensgrad.
    """
    
    def __init__(self, model=None):
        """Initialisera med valfri sklearn-modell."""
        self.model = model or RandomForestClassifier(
            n_estimators=50, 
            random_state=42
        )
        self.is_trained = False
        self.feature_names = []
    
    def create_features(self, df):
        """
        Skapa ML-features från OHLCV data.
        
        Args:
            df: DataFrame med kolumner ['open', 'high', 'low', 'close', 'volume']
        
        Returns:
            DataFrame med features för ML-modell
        """
        features = pd.DataFrame(index=df.index)
        
        # Prisrörelse features
        features['price_change_pct'] = df['close'].pct_change()
        features['price_volatility'] = df['close'].rolling(10).std()
        
        # Volym features
        features['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
        features['volume_change_pct'] = df['volume'].pct_change()
        
        # Enkla tekniska indikatorer
        features['sma_10'] = df['close'].rolling(10).mean()
        features['sma_20'] = df['close'].rolling(20).mean()
        features['price_vs_sma10'] = (df['close'] - features['sma_10']) / df['close']
        features['price_vs_sma20'] = (df['close'] - features['sma_20']) / df['close']
        features['sma_ratio'] = features['sma_10'] / features['sma_20']
        
        # High/Low features
        features['high_low_ratio'] = df['high'] / df['low']
        features['close_position'] = (df['close'] - df['low']) / (df['high'] - df['low'])
        
        self.feature_names = features.columns.tolist()
        return features.dropna()
    
    def create_labels(self, df, future_periods=5, threshold=0.02):
        """
        Skapa labels för trading (buy/hold signaler).
        
        Args:
            df: DataFrame med prisdata
            future_periods: Antal perioder framåt att titta på
            threshold: Minsta prisrörelse för buy-signal
        
        Returns:
            Series med binary labels (1=buy, 0=hold/sell)
        """
        future_returns = df['close'].shift(-future_periods) / df['close'] - 1
        labels = (future_returns > threshold).astype(int)
        return labels
    
    def train(self, df, test_size=0.2):
        """
        Träna modellen på historisk data.
        
        Args:
            df: DataFrame med OHLCV data
            test_size: Andel data för testing
        
        Returns:
            dict med träningsresultat
        """
        # Skapa features och labels
        features = self.create_features(df)
        labels = self.create_labels(df)
        
        # Matcha längder (labels kan vara kortare pga shift)
        min_length = min(len(features), len(labels))
        features = features.iloc[:min_length]
        labels = labels.iloc[:min_length]
        
        # Ta bort NaN värden
        valid_mask = ~(features.isna().any(axis=1) | labels.isna())
        features = features[valid_mask]
        labels = labels[valid_mask]
        
        if len(features) < 50:
            raise ValueError("För lite data för träning (behöver minst 50 exempel)")
        
        # Dela upp data
        X_train, X_test, y_train, y_test = train_test_split(
            features, labels, test_size=test_size, random_state=42, stratify=labels
        )
        
        # Träna modell
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # Evaluera
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        
        # Testa predict_proba
        train_probas = self.model.predict_proba(X_train)
        test_probas = self.model.predict_proba(X_test)
        
        return {
            'train_score': train_score,
            'test_score': test_score,
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_count': len(self.feature_names),
            'predict_proba_available': True,
            'class_distribution': dict(zip(*np.unique(y_train, return_counts=True)))
        }
    
    def predict_signal(self, df, confidence_threshold=0.6):
        """
        Generera trading-signal med konfidensgrad.
        
        Args:
            df: DataFrame med senaste OHLCV data
            confidence_threshold: Minsta konfidensgrad för signal
        
        Returns:
            dict med signal-information
        """
        if not self.is_trained:
            raise ValueError("Modellen måste tränas först")
        
        features = self.create_features(df)
        if len(features) == 0:
            return {"action": "hold", "confidence": 0.0, "reason": "Inga giltiga features"}
        
        # Använd senaste data-punkt
        latest_features = features.iloc[-1:][self.feature_names]
        
        # Förutsäg sannolikheter
        probabilities = self.model.predict_proba(latest_features)
        buy_probability = probabilities[0, 1]  # Sannolikhet för klass 1 (buy)
        
        # Generera signal baserat på konfidensgrad
        if buy_probability >= confidence_threshold:
            action = "buy"
            confidence = buy_probability
        elif buy_probability <= (1 - confidence_threshold):
            action = "sell"
            confidence = 1 - buy_probability
        else:
            action = "hold"
            confidence = max(buy_probability, 1 - buy_probability)
        
        return {
            "action": action,
            "confidence": float(confidence),
            "buy_probability": float(buy_probability),
            "sell_probability": float(1 - buy_probability),
            "features_used": len(self.feature_names)
        }


def example_usage():
    """Exempel på hur TradingMLPredictor används."""
    
    # Skapa syntetisk data för demo
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=200, freq='H')
    
    # Simulera OHLCV data
    close_prices = 100 + np.cumsum(np.random.normal(0, 1, 200))
    data = pd.DataFrame({
        'open': close_prices + np.random.normal(0, 0.5, 200),
        'high': close_prices + np.abs(np.random.normal(2, 1, 200)),
        'low': close_prices - np.abs(np.random.normal(2, 1, 200)),
        'close': close_prices,
        'volume': np.random.lognormal(10, 0.5, 200)
    }, index=dates)
    
    # Skapa och träna predictor
    predictor = TradingMLPredictor()
    
    print("Tränar ML-modell...")
    train_results = predictor.train(data[:-20])  # Spara sista 20 för test
    
    print(f"Träningsresultat:")
    for key, value in train_results.items():
        print(f"  {key}: {value}")
    
    # Testa förutsägelser
    print("\nGenererar trading-signaler...")
    test_data = data[-30:]  # Använd sista 30 punkter för features
    
    signal = predictor.predict_signal(test_data)
    print(f"Signal: {signal}")
    
    # Testa olika konfidensgrad-trösklar
    print("\nTesting olika konfidensgrad-trösklar:")
    for threshold in [0.5, 0.6, 0.7, 0.8]:
        signal = predictor.predict_signal(test_data, confidence_threshold=threshold)
        print(f"  Threshold {threshold}: {signal['action']} (confidence: {signal['confidence']:.3f})")


if __name__ == "__main__":
    example_usage()