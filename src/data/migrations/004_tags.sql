-- =============================================================================
-- Finance Tracker - Tags & Enhanced Notes (Phase 2.2)
-- =============================================================================

-- Tags table: Stores unique tag names
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    color TEXT,  -- Optional color for display (e.g., "blue", "green")
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Transaction tags junction table: Many-to-many relationship
CREATE TABLE IF NOT EXISTS transaction_tags (
    transaction_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (transaction_id, tag_id),
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

-- Indexes for efficient tag queries
CREATE INDEX IF NOT EXISTS idx_transaction_tags_transaction ON transaction_tags(transaction_id);
CREATE INDEX IF NOT EXISTS idx_transaction_tags_tag ON transaction_tags(tag_id);
CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

-- Add notes column to transactions if not exists (enhanced notes support)
-- SQLite doesn't support ALTER TABLE IF NOT EXISTS, so we check first
-- This will fail silently if column already exists, which is fine
