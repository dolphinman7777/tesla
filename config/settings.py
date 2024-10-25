import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
DUNE_API_KEY = os.getenv('DUNE_API_KEY')

# Cache settings
CACHE_TTL = 300  # 5 minutes
CACHE_ENABLED = True

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 100

# UI Settings
GREEN_TEXT = "\033[92m"
RESET_TEXT = "\033[0m"

# Query IDs - Replace these with your actual query IDs after creating them in Dune
QUERIES = {
    'token_metrics': 3373922,  # Your main token analysis query
    'token_price_prediction': 3373923,  # Price prediction query
    'token_correlation': 3373924,  # Token correlation analysis
    'token_sentiment': 3373925,  # Social sentiment analysis
    'token_whale_watching': 3373926,  # Whale movement tracking
    'token_defi_metrics': 3373927,  # DeFi-specific metrics
    'wallet_analysis': 2815547,  # This is just an example ID - you'll need to replace it
    'solana_analysis': 4202166,  # Your Solana query ID
}

# Trading Strategy Parameters
STRATEGY = {
    'min_market_cap': 1000000,  # Minimum market cap in USD
    'min_daily_volume': 100000,  # Minimum 24h volume in USD
    'max_price_impact': 0.02,   # Maximum acceptable price impact
    'min_holder_count': 1000    # Minimum number of holders
}
