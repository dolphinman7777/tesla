-- Query Name: Token Price and Metrics
-- Description: Gets current price, volume, and market metrics for any token
SELECT 
    p.price,
    p.symbol,
    COALESCE(v.volume_24h, 0) as volume_24h,
    COALESCE(m.market_cap, 0) as market_cap,
    COALESCE(h.holder_count, 0) as holder_count,
    COALESCE(t.total_transactions_24h, 0) as transactions_24h
FROM prices."usd" p
LEFT JOIN (
    SELECT 
        token_address,
        SUM(amount_usd) as volume_24h
    FROM dex."trades"
    WHERE block_time >= now() - interval '24 hours'
    GROUP BY token_address
) v ON v.token_address = p.contract_address
LEFT JOIN tokens.erc20 m ON m.contract_address = p.contract_address
LEFT JOIN (
    SELECT 
        token_address,
        COUNT(DISTINCT holder_address) as holder_count
    FROM erc20."token_balances"
    WHERE amount > 0
    GROUP BY token_address
) h ON h.token_address = p.contract_address
LEFT JOIN (
    SELECT 
        token_address,
        COUNT(*) as total_transactions_24h
    FROM dex."trades"
    WHERE block_time >= now() - interval '24 hours'
    GROUP BY token_address
) t ON t.token_address = p.contract_address
WHERE p.symbol = '{{token_symbol}}'
LIMIT 1
