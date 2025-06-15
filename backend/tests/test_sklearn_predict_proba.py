"""
Test för att verifiera att scikit-learn och predict_proba-funktionalitet fungerar korrekt.
"""
import numpy as np
import pytest
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification


def test_predict_proba_availability():
    """Testa att predict_proba metoden finns tillgänglig i scikit-learn klassificerare."""
    # Skapa en enkel klassificerare
    clf = RandomForestClassifier(random_state=42)
    
    # Verifiera att predict_proba metoden finns
    assert hasattr(clf, 'predict_proba'), "predict_proba metoden ska finnas i klassificeraren"
    
    # Verifiera att metoden är callable
    assert callable(getattr(clf, 'predict_proba')), "predict_proba ska vara en metod som kan anropas"


def test_predict_proba_functionality():
    """Testa att predict_proba faktiskt fungerar med tränade modeller."""
    # Skapa syntetisk data för klassificering
    X, y = make_classification(
        n_samples=100, 
        n_features=4, 
        n_classes=2, 
        random_state=42
    )
    
    # Dela upp data i träning och test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Träna modellen
    clf = RandomForestClassifier(n_estimators=10, random_state=42)
    clf.fit(X_train, y_train)
    
    # Testa predict_proba
    probabilities = clf.predict_proba(X_test)
    
    # Verifiera att sannolikheterna har rätt format
    assert probabilities.shape[0] == len(X_test), "Antal rader ska matcha antal test-exempel"
    assert probabilities.shape[1] == 2, "Antal kolumner ska matcha antal klasser (2)"
    
    # Verifiera att sannolikheterna summerar till 1 för varje exempel
    row_sums = np.sum(probabilities, axis=1)
    np.testing.assert_allclose(
        row_sums, 
        np.ones(len(X_test)), 
        rtol=1e-7,
        err_msg="Sannolikheter för varje exempel ska summera till 1"
    )
    
    # Verifiera att alla sannolikheter är mellan 0 och 1
    assert np.all(probabilities >= 0), "Alla sannolikheter ska vara >= 0"
    assert np.all(probabilities <= 1), "Alla sannolikheter ska vara <= 1"


def test_trading_relevant_classification_example():
    """
    Exempel på hur predict_proba kan användas för trading-relaterad klassificering.
    Detta visar hur metoden kan integreras i tradingstrategier.
    """
    # Simulera trading-relaterade features (pris-rörelser, volym, etc.)
    np.random.seed(42)
    n_samples = 200
    
    # Skapa features som kan representera tekniska indikatorer
    price_change = np.random.normal(0, 1, n_samples)  # Prisförändring
    volume_ratio = np.random.uniform(0.5, 2.0, n_samples)  # Volymförhållande
    rsi = np.random.uniform(0, 100, n_samples)  # RSI-indikator
    moving_avg_diff = np.random.normal(0, 0.5, n_samples)  # Moving average skillnad
    
    X = np.column_stack([price_change, volume_ratio, rsi, moving_avg_diff])
    
    # Skapa enkla trading-signaler (0=hold/sell, 1=buy) baserat på features
    # Detta är förenklat för test-syften
    y = ((price_change > 0) & (volume_ratio > 1.2) & (rsi < 70)).astype(int)
    
    # Träna modell
    clf = RandomForestClassifier(n_estimators=50, random_state=42)
    clf.fit(X, y)
    
    # Testa predict_proba för nya data
    new_data = np.array([[0.5, 1.5, 30, 0.2]])  # Bullish scenario
    probabilities = clf.predict_proba(new_data)
    
    # Verifiera format
    assert probabilities.shape == (1, 2), "Ska returnera sannolikheter för båda klasserna"
    
    # Hämta sannolikhet för buy-signal (klass 1)
    buy_probability = probabilities[0, 1]
    
    assert 0 <= buy_probability <= 1, "Buy-sannolikhet ska vara mellan 0 och 1"
    
    # Detta visar hur predict_proba kan användas för konfidensbaserad trading
    confidence_threshold = 0.7
    if buy_probability > confidence_threshold:
        signal = "strong_buy"
    elif buy_probability > 0.5:
        signal = "weak_buy"
    else:
        signal = "hold_or_sell"
    
    assert signal in ["strong_buy", "weak_buy", "hold_or_sell"], "Signal ska vara giltig"


def test_sklearn_version():
    """Testa att rätt version av scikit-learn är installerad."""
    import sklearn
    
    # Verifiera att vi har en kompatibel version
    version = sklearn.__version__
    major, minor = map(int, version.split('.')[:2])
    
    # predict_proba har funnits sedan tidiga versioner, men vi vill ha en relativt ny version
    assert major >= 1, f"scikit-learn major version ska vara >= 1, nuvarande: {version}"
    
    if major == 1:
        assert minor >= 0, f"För scikit-learn 1.x, minor version ska vara >= 0, nuvarande: {version}"