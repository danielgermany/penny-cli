-- =============================================================================
-- Finance Tracker - Planned Purchases (Phase 2.4)
-- =============================================================================

CREATE TABLE IF NOT EXISTS planned_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,

    -- Purchase details
    name TEXT NOT NULL,
    description TEXT,
    estimated_cost DECIMAL(12,2) NOT NULL,
    actual_cost DECIMAL(12,2),

    -- Priority and categorization
    priority INTEGER NOT NULL DEFAULT 3,  -- 1=Critical/Necessity, 2=High, 3=Moderate, 4=Low, 5=Want
    category TEXT,  -- Same categories as transactions

    -- Timeline
    deadline DATE,  -- Optional target purchase date
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Status tracking
    status TEXT DEFAULT 'planned',  -- 'planned', 'purchased', 'cancelled'
    purchased_at TIMESTAMP,
    purchased_transaction_id INTEGER,  -- Link to actual transaction

    -- Additional info
    notes TEXT,
    url TEXT,  -- Optional link to product page

    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (purchased_transaction_id) REFERENCES transactions(id)
);

CREATE INDEX IF NOT EXISTS idx_planned_purchases_user ON planned_purchases(user_id);
CREATE INDEX IF NOT EXISTS idx_planned_purchases_status ON planned_purchases(status);
CREATE INDEX IF NOT EXISTS idx_planned_purchases_priority ON planned_purchases(priority);
CREATE INDEX IF NOT EXISTS idx_planned_purchases_deadline ON planned_purchases(deadline);
