/*
Table(s): solana.transactions
Reason: Raw tables recommended

Table(s): solana_utils.token_accounts
Reason: Curated dataset recommendations

Table(s): solana_oms_proxy_solana.solana_oms_proxy_call_withdraw
Reason: Based on contract addresses or possible project names

*/

-- Title: Solana Wallet Analysis
-- Parameters: {{wallet_address}} (text)

WITH wallet_transactions AS (
    SELECT 
        signer as wallet,
        COUNT(*) as tx_count,
        COUNT(DISTINCT block_date) as active_days,
        MIN(block_date) as first_tx_date,
        MAX(block_date) as last_tx_date,
        SUM(fee) / 1e9 as total_fees_sol
    FROM solana.transactions
    WHERE 
        signer = '{{wallet_address}}'
        AND block_date >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY signer
),

token_transfers AS (
    SELECT 
        COALESCE(COUNT(*), 0) as token_transfer_count,
        COALESCE(COUNT(DISTINCT mint), 0) as unique_tokens_transferred
    FROM solana.transfers
    WHERE 
        (from_address = '{{wallet_address}}' OR to_address = '{{wallet_address}}')
        AND block_date >= CURRENT_DATE - INTERVAL '30' DAY
)

SELECT 
    w.wallet,
    w.tx_count as total_transactions,
    w.active_days,
    w.first_tx_date,
    w.last_tx_date,
    w.total_fees_sol,
    t.token_transfer_count,
    t.unique_tokens_transferred,
    CASE 
        WHEN w.tx_count > 1000 THEN 'Whale 🐋'
        WHEN w.tx_count > 100 THEN 'Dolphin 🐬'
        ELSE 'Fish 🐟'
    END as wallet_category
FROM wallet_transactions w
CROSS JOIN token_transfers t;
