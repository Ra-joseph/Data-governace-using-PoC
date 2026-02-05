-- Sample Data for Financial Demo
-- Includes intentional data quality issues for demonstration

-- Insert Customer Accounts (10 records)
INSERT INTO customer_accounts (customer_email, customer_ssn, customer_phone, first_name, last_name, date_of_birth, account_type, account_status, credit_limit, current_balance, created_at, last_login) VALUES
('john.doe@email.com', '123-45-6789', '+1-555-0101', 'John', 'Doe', '1985-03-15', 'checking', 'active', NULL, 5240.75, '2023-01-15 10:30:00', '2024-02-03 14:22:00'),
('jane.smith@email.com', '234-56-7890', '+1-555-0102', 'Jane', 'Smith', '1990-07-22', 'savings', 'active', NULL, 12500.00, '2023-02-20 09:15:00', '2024-02-04 08:15:00'),
('bob.wilson@email.com', '345-67-8901', '+1-555-0103', 'Bob', 'Wilson', '1978-11-30', 'credit', 'active', 10000.00, -2340.50, '2023-03-10 14:45:00', '2024-02-03 19:45:00'),
('alice.brown@email.com', '456-78-9012', '+1-555-0104', 'Alice', 'Brown', '1995-05-18', 'checking', 'active', NULL, 8750.25, '2023-04-05 11:20:00', '2024-02-04 07:30:00'),
('charlie.davis@email.com', '567-89-0123', '+1-555-0105', 'Charlie', 'Davis', '1982-09-08', 'credit', 'suspended', 5000.00, -4890.00, '2023-05-12 16:00:00', '2024-01-28 22:10:00'),
('emma.johnson@email.com', '678-90-1234', '+1-555-0106', 'Emma', 'Johnson', '1988-12-25', 'savings', 'active', NULL, 25000.00, '2023-06-18 13:30:00', '2024-02-03 16:20:00'),
('david.miller@email.com', '789-01-2345', '+1-555-0107', 'David', 'Miller', '1992-04-14', 'checking', 'active', NULL, 3210.00, '2023-07-22 10:10:00', '2024-02-04 09:05:00'),
('sophia.taylor@email.com', '890-12-3456', '+1-555-0108', 'Sophia', 'Taylor', '1987-08-03', 'credit', 'active', 15000.00, -1250.75, '2023-08-30 15:45:00', '2024-02-03 20:30:00'),
('michael.anderson@email.com', '901-23-4567', '+1-555-0109', 'Michael', 'Anderson', '1980-01-20', 'savings', 'active', NULL, 42000.00, '2023-09-14 12:00:00', '2024-02-02 11:45:00'),
('olivia.thomas@email.com', '012-34-5678', '+1-555-0110', 'Olivia', 'Thomas', '1993-06-12', 'checking', 'closed', NULL, 0.00, '2023-10-05 09:30:00', '2024-01-15 14:00:00');

-- Insert Transactions (23 records with suspicious patterns)
INSERT INTO transactions (account_id, transaction_type, amount, merchant_name, merchant_category, transaction_date, posted_date, description, status, currency_code, foreign_transaction_fee) VALUES
-- Normal transactions
(1, 'debit', -45.50, 'Starbucks', 'Food & Dining', '2024-02-01 08:15:00', '2024-02-01 08:15:00', 'Coffee purchase', 'posted', 'USD', 0.00),
(1, 'debit', -120.00, 'Whole Foods', 'Groceries', '2024-02-01 18:30:00', '2024-02-01 18:30:00', 'Grocery shopping', 'posted', 'USD', 0.00),
(2, 'credit', 3000.00, 'Payroll Deposit', 'Income', '2024-02-01 00:00:00', '2024-02-01 00:00:00', 'Salary deposit', 'posted', 'USD', 0.00),
(3, 'debit', -89.99, 'Amazon', 'Shopping', '2024-02-01 14:20:00', '2024-02-02 14:20:00', 'Online purchase', 'posted', 'USD', 0.00),
(4, 'debit', -1200.00, 'Rent Payment', 'Bills', '2024-02-01 09:00:00', '2024-02-01 09:00:00', 'Monthly rent', 'posted', 'USD', 0.00),

-- Suspicious Pattern 1: Large unusual purchases (Account 5 - Charlie Davis)
(5, 'debit', -3500.00, 'Electronics Store', 'Electronics', '2024-01-28 15:30:00', '2024-01-28 15:30:00', 'Large electronics purchase', NULL, 'USD', 0.00),
(5, 'debit', -2800.00, 'Jewelry Store', 'Luxury', '2024-01-28 16:45:00', '2024-01-28 16:45:00', 'Jewelry purchase', NULL, 'USD', 0.00),

-- Suspicious Pattern 2: Late-night ATM withdrawals
(3, 'withdrawal', -500.00, 'ATM Withdrawal', 'Cash', '2024-02-02 02:30:00', '2024-02-02 02:30:00', 'ATM cash withdrawal', 'posted', 'USD', 0.00),
(3, 'withdrawal', -500.00, 'ATM Withdrawal', 'Cash', '2024-02-02 02:45:00', '2024-02-02 02:45:00', 'ATM cash withdrawal', 'posted', 'USD', 0.00),

-- Suspicious Pattern 3: Rapid repeated small transactions
(3, 'debit', -9.99, 'Gas Station', 'Gas', '2024-02-03 10:05:00', '2024-02-03 10:05:00', 'Gas purchase', 'posted', 'USD', 0.00),
(3, 'debit', -9.99, 'Gas Station', 'Gas', '2024-02-03 10:07:00', '2024-02-03 10:07:00', 'Gas purchase', 'posted', 'USD', 0.00),
(3, 'debit', -9.99, 'Gas Station', 'Gas', '2024-02-03 10:10:00', '2024-02-03 10:10:00', 'Gas purchase', 'posted', 'USD', 0.00),

-- Normal transactions continued
(6, 'credit', 5000.00, 'Investment Return', 'Income', '2024-02-02 12:00:00', '2024-02-02 12:00:00', 'Investment dividend', 'posted', 'USD', 0.00),
(7, 'debit', -250.00, 'Utility Company', 'Bills', '2024-02-02 10:30:00', '2024-02-02 10:30:00', 'Electric bill', 'posted', 'USD', 0.00),
(8, 'debit', -180.50, 'Restaurant', 'Food & Dining', '2024-02-03 19:00:00', '2024-02-03 19:00:00', 'Dinner', 'posted', 'USD', 0.00),

-- Foreign transaction with fee
(8, 'debit', -450.00, 'Hotel Paris', 'Travel', '2024-02-03 08:00:00', '2024-02-04 08:00:00', 'Hotel booking', 'pending', 'EUR', 13.50),

-- More normal transactions
(1, 'debit', -65.00, 'Gym Membership', 'Health', '2024-02-03 06:00:00', '2024-02-03 06:00:00', 'Monthly gym fee', 'posted', 'USD', 0.00),
(4, 'transfer', -500.00, 'Savings Account', 'Transfer', '2024-02-03 15:00:00', '2024-02-03 15:00:00', 'Transfer to savings', 'posted', 'USD', 0.00),
(9, 'credit', 100.00, 'Interest Payment', 'Income', '2024-02-01 00:00:00', '2024-02-01 00:00:00', 'Monthly interest', 'posted', 'USD', 0.00),

-- Data quality issue: NULL status
(2, 'debit', -75.30, 'Pharmacy', 'Health', '2024-02-04 11:00:00', NULL, 'Prescription pickup', NULL, 'USD', 0.00),

-- Pending transactions
(1, 'debit', -35.00, 'Gas Station', 'Gas', '2024-02-04 07:30:00', NULL, 'Gas purchase', 'pending', 'USD', 0.00),
(4, 'debit', -12.50, 'Coffee Shop', 'Food & Dining', '2024-02-04 08:00:00', NULL, 'Morning coffee', 'pending', 'USD', 0.00),
(7, 'debit', -95.00, 'Department Store', 'Shopping', '2024-02-04 13:00:00', NULL, 'Clothing purchase', 'pending', 'USD', 0.00);

-- Insert Fraud Alerts (6 records)
INSERT INTO fraud_alerts (transaction_id, account_id, alert_type, risk_score, alert_reason, alert_status, detected_at, resolved_at, resolved_by, resolution_notes, false_positive) VALUES
-- Confirmed fraud case
(6, 5, 'large_purchase', 95.5, 'Unusually large purchase exceeding 70% of credit limit', 'confirmed_fraud', '2024-01-28 15:31:00', '2024-01-29 10:00:00', 'fraud_team_lead', 'Customer confirmed unauthorized purchase. Card blocked and refund processed.', FALSE),
(7, 5, 'velocity', 98.2, 'Multiple high-value transactions within short timeframe', 'confirmed_fraud', '2024-01-28 16:46:00', '2024-01-29 10:00:00', 'fraud_team_lead', 'Part of same fraud incident. Account suspended.', FALSE),

-- Late-night withdrawals (false positive)
(8, 3, 'unusual_activity', 72.0, 'Late-night ATM withdrawals in rapid succession', 'false_positive', '2024-02-02 02:31:00', '2024-02-02 09:15:00', 'fraud_analyst_1', 'Customer verified legitimate withdrawals during travel.', TRUE),
(9, 3, 'velocity', 75.5, 'Multiple cash withdrawals within 15 minutes', 'false_positive', '2024-02-02 02:46:00', '2024-02-02 09:15:00', 'fraud_analyst_1', 'Legitimate activity during travel.', TRUE),

-- Rapid small transactions (under investigation)
(10, 3, 'velocity', 68.0, 'Multiple small transactions at same merchant within minutes', 'investigating', '2024-02-03 10:11:00', NULL, NULL, NULL, FALSE),

-- Data quality issue: Missing risk_score (NULL)
(16, 8, 'location', NULL, 'Foreign transaction detected from new location', 'investigating', '2024-02-03 08:01:00', NULL, NULL, NULL, FALSE);

-- Update account statuses based on fraud
UPDATE customer_accounts SET account_status = 'suspended' WHERE account_id = 5;
