-- NASDAQ Constituents (şirket listesi)
CREATE TABLE IF NOT EXISTS nasdaq_constituents (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    weight_pct DECIMAL(5,2),
    sector TEXT,
    market_cap BIGINT,
    last_earnings_date DATE,
    next_earnings_date DATE,
    earnings_time TEXT,
    importance_level TEXT DEFAULT 'MEDIUM',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Earnings Events (kazanç takvimi)
CREATE TABLE IF NOT EXISTS earnings_events (
    id SERIAL PRIMARY KEY,
    symbol TEXT NOT NULL REFERENCES nasdaq_constituents(symbol),
    date DATE NOT NULL,
    time TEXT, -- 'BMO', 'AMC', 'TNS'
    expected_eps DECIMAL(10,4),
    expected_revenue DECIMAL(15,2),
    actual_eps DECIMAL(10,4),
    actual_revenue DECIMAL(15,2),
    guidance TEXT, -- 'up', 'down', 'maintain'
    guidance_value TEXT,
    is_announced BOOLEAN DEFAULT FALSE,
    nasdaq_impact_score DECIMAL(5,2),
    scenario_type TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(symbol, date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_earnings_date ON earnings_events(date);
CREATE INDEX IF NOT EXISTS idx_earnings_symbol ON earnings_events(symbol);
CREATE INDEX IF NOT EXISTS idx_constituents_importance ON nasdaq_constituents(importance_level);
CREATE INDEX IF NOT EXISTS idx_constituents_next_earnings ON nasdaq_constituents(next_earnings_date);

-- Initial NASDAQ-100 Top 20 Data
INSERT INTO nasdaq_constituents (symbol, name, weight_pct, sector, importance_level) VALUES
('AAPL', 'Apple Inc.', 12.45, 'Technology', 'CRITICAL'),
('MSFT', 'Microsoft Corp.', 11.23, 'Technology', 'CRITICAL'),
('AMZN', 'Amazon.com Inc.', 7.85, 'Consumer Discretionary', 'CRITICAL'),
('NVDA', 'NVIDIA Corp.', 6.92, 'Technology', 'CRITICAL'),
('GOOGL', 'Alphabet Class A', 6.12, 'Communication', 'CRITICAL'),
('META', 'Meta Platforms', 4.78, 'Communication', 'CRITICAL'),
('TSLA', 'Tesla Inc.', 4.52, 'Consumer Discretionary', 'CRITICAL'),
('AVGO', 'Broadcom Inc.', 3.21, 'Technology', 'HIGH'),
('COST', 'Costco Wholesale', 2.89, 'Consumer Staples', 'HIGH'),
('NFLX', 'Netflix Inc.', 2.45, 'Communication', 'HIGH'),
('AMD', 'Advanced Micro Devices', 2.34, 'Technology', 'HIGH'),
('ADBE', 'Adobe Inc.', 2.12, 'Technology', 'HIGH'),
('PEP', 'PepsiCo Inc.', 1.98, 'Consumer Staples', 'MEDIUM'),
('CSCO', 'Cisco Systems', 1.87, 'Technology', 'MEDIUM'),
('INTC', 'Intel Corp.', 1.76, 'Technology', 'MEDIUM'),
('QCOM', 'Qualcomm Inc.', 1.65, 'Technology', 'MEDIUM'),
('CMCSA', 'Comcast Corp.', 1.54, 'Communication', 'MEDIUM'),
('TXN', 'Texas Instruments', 1.43, 'Technology', 'MEDIUM'),
('INTU', 'Intuit Inc.', 1.32, 'Technology', 'MEDIUM'),
('AMGN', 'Amgen Inc.', 1.21, 'Healthcare', 'MEDIUM')
ON CONFLICT (symbol) DO UPDATE SET
    weight_pct = EXCLUDED.weight_pct,
    importance_level = EXCLUDED.importance_level,
    updated_at = NOW();

-- RLS Policies
ALTER TABLE nasdaq_constituents ENABLE ROW LEVEL SECURITY;
ALTER TABLE earnings_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access" ON nasdaq_constituents FOR SELECT USING (true);
CREATE POLICY "Public read access" ON earnings_events FOR SELECT USING (true);
