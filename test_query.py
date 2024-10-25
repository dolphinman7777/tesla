import asyncio
from core.dune_manager import DuneManager
from models.query_types import QueryIntent, QueryResult

async def test_solana_query():
    # Initialize the Dune manager
    dune = DuneManager()
    
    # Test Solana wallet (example address)
    test_wallet = 'CEWZxvpuUhxe1KL4cK3NaVhF3py1YLDHXz7uGJ6UjBiF'
    
    # Create a test intent
    test_intent = QueryIntent(
        query_type='solana_analysis',
        parameters={
            'wallet_address': test_wallet
        }
    )
    
    # Execute query
    print(f"Executing Solana analysis for wallet: {test_wallet}")
    result = await dune.execute_query(test_intent)
    
    # Print results
    if result.success and result.data:
        print("\nSolana Wallet Analysis:")
        print(f"Wallet: {test_wallet[:6]}...{test_wallet[-4:]}")
        print(f"Total Transactions: {result.data['total_transactions']:,}")
        print(f"Active Days: {result.data['active_days']}")
        print(f"Token Transfers: {result.data['token_transfer_count']:,}")
        print(f"Unique Tokens: {result.data['unique_tokens_transferred']:,}")
        print(f"Total Fees (SOL): {float(result.data['total_fees_sol']):.4f}")
        print(f"Wallet Category: {result.data['wallet_category']}")
        print(f"\nFirst Transaction: {result.data['first_tx_date']}")
        print(f"Last Transaction: {result.data['last_tx_date']}")
    else:
        print(f"Query failed: {result.error}")

if __name__ == "__main__":
    asyncio.run(test_solana_query())
