-- =============================================================================
-- Finance Tracker - Recurring Charges (Phase 1.2)
-- =============================================================================

CREATE TABLE IF NOT EXISTS recurring_charges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Identity
    merchant TEXT NOT NULL,
    category TEXT NOT NULL,

    -- Pattern
    typical_amount DECIMAL(12,2),
    frequency TEXT NOT NULL,         -- 'weekly', 'monthly', 'annual'
    day_of_period INTEGER,           -- Day of week (0-6) or day of month (1-31)

    -- Tracking
    next_expected_date DATE,
    first_seen DATE NOT NULL,
    last_seen DATE NOT NULL,
    occurrence_count INTEGER DEFAULT 1,

    -- Status
    status TEXT DEFAULT 'active',    -- 'active', 'paused', 'cancelled'
    confidence DECIMAL(3,2) DEFAULT 0.5,  -- Pattern detection confidence

    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_recurring_user ON recurring_charges(user_id);
CREATE INDEX IF NOT EXISTS idx_recurring_merchant ON recurring_charges(merchant);
CREATE INDEX IF NOT EXISTS idx_recurring_status ON recurring_charges(status);
CREATE INDEX IF NOT EXISTS idx_recurring_next_date ON recurring_charges(next_expected_date);
