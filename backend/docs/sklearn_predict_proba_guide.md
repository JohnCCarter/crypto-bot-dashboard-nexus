# Användning av predict_proba för Trading ML-modeller

Detta dokument beskriver hur man använder `predict_proba`-metoden från scikit-learn i trading-sammanhang.

## Översikt

`predict_proba` är en metod som finns i de flesta klassificeringsmodeller från scikit-learn. Den returnerar sannolikheter för varje klass istället för bara den förutsagda klassen, vilket ger mer detaljerad information om modellens konfidensgrad.

## Installation

Scikit-learn är redan inkluderat i projektets requirements.txt:

```
scikit-learn==1.7.0
```

För att installera alla dependencies:

```bash
cd backend
pip install -r requirements.txt
```

## Grundläggande Användning

```python
from sklearn.ensemble import RandomForestClassifier
import numpy as np

# Skapa och träna modell
clf = RandomForestClassifier()
clf.fit(X_train, y_train)

# Använd predict_proba för sannolikheter
probabilities = clf.predict_proba(X_test)

# probabilities[i, j] = sannolikhet för sample i att tillhöra klass j
```

## Trading-specifik Användning

### Exempel 1: Buy/Sell Signal med Konfidensgrad

```python
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np

def create_trading_features(df):
    """Skapa features från OHLCV data för ML-modell."""
    features = pd.DataFrame()
    
    # Prisrörelse features
    features['price_change_pct'] = df['close'].pct_change()
    features['volume_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # Tekniska indikatorer
    features['rsi'] = calculate_rsi(df['close'])  # Din RSI-implementering
    features['ma_diff'] = (df['close'] - df['close'].rolling(20).mean()) / df['close']
    
    return features.dropna()

def predict_trading_signal(model, features):
    """Förutsäg trading-signal med konfidensgrad."""
    probabilities = model.predict_proba(features)
    
    # Antag klasser: 0=sell/hold, 1=buy
    buy_probability = probabilities[:, 1]
    
    # Skapa signaler baserat på sannolikhet
    signals = []
    for prob in buy_probability:
        if prob > 0.8:
            signals.append({"action": "strong_buy", "confidence": prob})
        elif prob > 0.6:
            signals.append({"action": "buy", "confidence": prob})
        elif prob < 0.2:
            signals.append({"action": "strong_sell", "confidence": 1 - prob})
        elif prob < 0.4:
            signals.append({"action": "sell", "confidence": 1 - prob})
        else:
            signals.append({"action": "hold", "confidence": 0.5})
    
    return signals
```

### Exempel 2: Riskhantering baserat på Modellkonfidensgrad

```python
def calculate_position_size(base_size, confidence, min_confidence=0.6):
    """Justera positionsstorlek baserat på modellkonfidensgrad."""
    if confidence < min_confidence:
        return 0  # Ingen position om låg konfidensgrad
    
    # Skalera positionsstorlek med konfidensgrad
    confidence_factor = (confidence - min_confidence) / (1.0 - min_confidence)
    return base_size * confidence_factor

# Användning
probabilities = model.predict_proba(current_features)
buy_confidence = probabilities[0, 1]

if buy_confidence > 0.6:
    position_size = calculate_position_size(
        base_size=1000,  # Bas positionsstorlek
        confidence=buy_confidence
    )
    print(f"Buy signal med konfidensgrad {buy_confidence:.2f}")
    print(f"Rekommenderad positionsstorlek: {position_size:.2f}")
```

### Exempel 3: Ensemble med Flera Modeller

```python
def ensemble_predict_proba(models, features):
    """Kombinera förutsägelser från flera modeller."""
    all_probabilities = []
    
    for model in models:
        probs = model.predict_proba(features)
        all_probabilities.append(probs)
    
    # Genomsnitt av alla modellers sannolikheter
    ensemble_probs = np.mean(all_probabilities, axis=0)
    
    return ensemble_probs

# Träna flera modeller
models = [
    RandomForestClassifier(n_estimators=100),
    GradientBoostingClassifier(),
    LogisticRegression()
]

for model in models:
    model.fit(X_train, y_train)

# Använd ensemble för förutsägelse
ensemble_probabilities = ensemble_predict_proba(models, X_test)
```

## Fördelar med predict_proba i Trading

1. **Konfidensgrad**: Ger information om hur säker modellen är på sina förutsägelser
2. **Riskhantering**: Möjliggör anpassning av positionsstorlek baserat på osäkerhet
3. **Flexibla Tröskelvärden**: Kan sätta olika gränser för olika signalstyrkor
4. **Ensemble-metoder**: Kan kombinera flera modellers sannolikheter

## Testning

Kör testerna för att verifiera att predict_proba fungerar korrekt:

```bash
python -m pytest backend/tests/test_sklearn_predict_proba.py -v
```

## Tips för Bästa Praxis

1. **Kalibrera Sannolikheter**: Använd `CalibratedClassifierCV` för bättre sannolikhetskalibrering
2. **Cross-validation**: Använd tidsserie cross-validation för trading-data
3. **Feature Engineering**: Inkludera relevanta tekniska indikatorer som features
4. **Undvik Lookahead Bias**: Se till att features endast använder historisk data
5. **Regular Retraining**: Uppdatera modeller regelbundet med ny data