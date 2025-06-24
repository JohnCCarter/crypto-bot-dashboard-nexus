-- ============================================
-- 🗄️ SUPABASE MINIMAL SCHEMA (CLEAN START)
-- ============================================
-- Kör detta i Supabase SQL Editor

-- ============================================
-- 📊 TRADES TABLE (Minimal)
-- ============================================
CREATE TABLE trades (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    cost DECIMAL(20, 8) NOT NULL,
    status VARCHAR(20) DEFAULT 'open',
    strategy VARCHAR(50),
    pnl DECIMAL(20, 8) DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 🎯 POSITIONS TABLE (Minimal)
-- ============================================
CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    side VARCHAR(10) NOT NULL,
    size DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    current_price DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8) DEFAULT 0,
    strategy VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    opened_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- ⚠️ RISK METRICS TABLE (Critical!)
-- ============================================
CREATE TABLE risk_metrics (
    id BIGSERIAL PRIMARY KEY,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    daily_pnl DECIMAL(20, 8) DEFAULT 0,
    total_trades INTEGER DEFAULT 0,
    trading_allowed BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date)
);

-- ============================================
-- 🚨 ALERTS TABLE
-- ============================================
CREATE TABLE alerts (
    id BIGSERIAL PRIMARY KEY,
    type VARCHAR(20) NOT NULL,
    severity VARCHAR(10) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    acknowledged BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 📈 ORDERS TABLE
-- ============================================
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    type VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,
    amount DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8),
    status VARCHAR(20) DEFAULT 'pending',
    strategy VARCHAR(50),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- 📊 BASIC INDEXES
-- ============================================
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_status ON trades(status);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_risk_metrics_date ON risk_metrics(date);
CREATE INDEX idx_alerts_type ON alerts(type);

-- ============================================
-- ✅ VERIFICATION
-- ============================================
SELECT 'All tables created successfully!' as status;