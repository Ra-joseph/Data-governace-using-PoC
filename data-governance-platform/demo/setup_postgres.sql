-- Setup script for Financial Demo Database
-- This creates the schema for the data governance demo

-- Drop tables if they exist
DROP TABLE IF EXISTS fraud_alerts CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS customer_accounts CASCADE;

-- Customer Accounts Table (CONTAINS PII - Intentional Policy Violations)
CREATE TABLE customer_accounts (
    account_id SERIAL PRIMARY KEY,
    customer_email VARCHAR(255) NOT NULL,  -- PII
    customer_ssn VARCHAR(11),              -- PII - VIOLATION: No encryption documented
    customer_phone VARCHAR(20),            -- PII
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,                    -- PII
    account_type VARCHAR(20) NOT NULL,     -- checking, savings, credit
    account_status VARCHAR(20) NOT NULL,   -- active, suspended, closed
    credit_limit DECIMAL(12, 2),
    current_balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

COMMENT ON TABLE customer_accounts IS 'Customer account information - CONTAINS PII';
COMMENT ON COLUMN customer_accounts.customer_ssn IS 'Social Security Number - SENSITIVE DATA';
COMMENT ON COLUMN customer_accounts.customer_email IS 'Customer email address';
COMMENT ON COLUMN customer_accounts.date_of_birth IS 'Date of birth - SENSITIVE DATA';

-- Transactions Table (Time-sensitive data - VIOLATION: Missing freshness SLA)
CREATE TABLE transactions (
    transaction_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES customer_accounts(account_id),
    transaction_type VARCHAR(50) NOT NULL,  -- debit, credit, transfer, withdrawal
    amount DECIMAL(12, 2) NOT NULL,
    merchant_name VARCHAR(255),
    merchant_category VARCHAR(100),
    transaction_date TIMESTAMP NOT NULL,
    posted_date TIMESTAMP,
    description TEXT,
    status VARCHAR(20),                     -- VIOLATION: No enum constraint, allows NULL
    currency_code VARCHAR(3) DEFAULT 'USD',
    foreign_transaction_fee DECIMAL(8, 2) DEFAULT 0.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE transactions IS 'Financial transactions - Time-sensitive data';

CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_status ON transactions(status);

-- Fraud Alerts Table (Critical data - VIOLATION: Missing quality thresholds)
CREATE TABLE fraud_alerts (
    alert_id SERIAL PRIMARY KEY,
    transaction_id INTEGER REFERENCES transactions(transaction_id),
    account_id INTEGER NOT NULL REFERENCES customer_accounts(account_id),
    alert_type VARCHAR(50) NOT NULL,        -- unusual_activity, large_purchase, velocity, location
    risk_score DECIMAL(5, 2),               -- VIOLATION: Some records have NULL risk_score
    alert_reason TEXT NOT NULL,
    alert_status VARCHAR(20) NOT NULL,      -- investigating, confirmed_fraud, false_positive, resolved
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    resolved_by VARCHAR(100),
    resolution_notes TEXT,
    false_positive BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE fraud_alerts IS 'Fraud detection alerts - Critical data';

CREATE INDEX idx_fraud_alerts_account ON fraud_alerts(account_id);
CREATE INDEX idx_fraud_alerts_status ON fraud_alerts(alert_status);
