-- =============================================================================
-- Finance Tracker - User Authentication (Phase 2.3)
-- =============================================================================

-- Add password hash field to users table
ALTER TABLE users ADD COLUMN password_hash TEXT;

-- Add last login tracking
ALTER TABLE users ADD COLUMN last_login TIMESTAMP;

-- Add user settings for authentication
ALTER TABLE users ADD COLUMN require_password BOOLEAN DEFAULT 0;
