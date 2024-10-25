import re
from typing import Optional, List
from models.query_types import QueryIntent
from config.ai_persona import TRAITS

class NLPProcessor:
    def __init__(self):
        self.intent_patterns = {
            # Basic price and market metrics
            'token_metrics': [
                r'(?:price|cost|worth|value).*?(?:of\s+)?(\$?[A-Z0-9]+)',
                r'(?:how\s+much\s+is).*?(\$?[A-Z0-9]+)',
                r'tell\s+me\s+about.*?(\$?[A-Z0-9]+)'
            ],
            # Price prediction and analysis
            'token_price_prediction': [
                r'(?:predict|forecast|expect).*?(?:price).*?(\$?[A-Z0-9]+)',
                r'(?:will|should).*?(\$?[A-Z0-9]+).*?(?:go up|rise|moon)',
                r'(?:bearish|bullish).*?(\$?[A-Z0-9]+)'
            ],
            # Token correlation analysis
            'token_correlation': [
                r'(?:correlation|relationship).*?(\$?[A-Z0-9]+).*?(\$?[A-Z0-9]+)',
                r'(?:compare|vs|versus).*?(\$?[A-Z0-9]+).*?(\$?[A-Z0-9]+)'
            ],
            # Social sentiment analysis
            'token_sentiment': [
                r'(?:sentiment|feeling|mood).*?(\$?[A-Z0-9]+)',
                r'(?:what\s+do\s+people\s+think).*?(\$?[A-Z0-9]+)',
                r'(?:social|twitter|telegram).*?(\$?[A-Z0-9]+)'
            ],
            # Whale watching
            'token_whale_watching': [
                r'(?:whale|large holder|big player).*?(\$?[A-Z0-9]+)',
                r'(?:movement|transfer|transaction).*?(\$?[A-Z0-9]+)'
            ],
            # DeFi metrics
            'token_defi_metrics': [
                r'(?:liquidity|pool|swap).*?(\$?[A-Z0-9]+)',
                r'(?:yield|apy|apr).*?(\$?[A-Z0-9]+)',
                r'(?:staking|farming).*?(\$?[A-Z0-9]+)'
            ],
            'wallet_analysis': [
                r'(?:wallet|address).*?(?:0x[a-fA-F0-9]{40})',
                r'(?:check|analyze|show).*?(?:wallet|address).*?(?:0x[a-fA-F0-9]{40})',
                r'(?:0x[a-fA-F0-9]{40}).*?(?:holdings|balance|activity)'
            ]
        }
        self.traits = TRAITS
        
    def extract_tokens(self, text: str) -> List[str]:
        tokens = re.findall(r'\$?([A-Z0-9]+)', text.upper())
        return [t for t in tokens if t]
        
    def extract_time_period(self, text: str) -> str:
        time_patterns = {
            'hour': r'(?:1h|hour|hourly)',
            'day': r'(?:24h|day|daily)',
            'week': r'(?:7d|week|weekly)',
            'month': r'(?:30d|month|monthly)',
            'year': r'(?:365d|year|yearly)'
        }
        
        for period, pattern in time_patterns.items():
            if re.search(pattern, text, re.I):
                return period
        return 'day'  # default
        
    def extract_trading_signals(self, text: str) -> dict:
        signals = {
            'action': None,  # buy, sell, hold
            'confidence': None,  # high, medium, low
            'urgency': None,  # immediate, soon, watch
        }
        
        # Action detection
        if re.search(r'(?:buy|long|bullish)', text, re.I):
            signals['action'] = 'buy'
        elif re.search(r'(?:sell|short|bearish)', text, re.I):
            signals['action'] = 'sell'
        elif re.search(r'(?:hold|wait|watch)', text, re.I):
            signals['action'] = 'hold'
            
        # Confidence detection
        if re.search(r'(?:definitely|certainly|sure|strong)', text, re.I):
            signals['confidence'] = 'high'
        elif re.search(r'(?:might|maybe|possibly)', text, re.I):
            signals['confidence'] = 'low'
        else:
            signals['confidence'] = 'medium'
            
        return signals
        
    def parse_input(self, text: str) -> QueryIntent:
        text_lower = text.lower()
        
        # Determine primary intent
        query_type = 'token_metrics'  # default
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    query_type = intent
                    break
                    
        tokens = self.extract_tokens(text)
        time_period = self.extract_time_period(text_lower)
        trading_signals = self.extract_trading_signals(text_lower)
        
        # Add trait-aware processing
        for category, traits in self.traits.items():
            for trait, description in traits.items():
                if any(keyword in text.lower() for keyword in trait.split('_')):
                    # Adjust query intent based on relevant traits
                    # This could involve setting specific parameters or adjusting the query type
                    pass
        
        return QueryIntent(
            query_type=query_type,
            parameters={
                'token_symbol': tokens[0] if tokens else None,
                'comparison_token': tokens[1] if len(tokens) > 1 else None,
                'signals': trading_signals
            },
            time_period=time_period
        )

    def extract_wallet_address(self, text: str) -> Optional[str]:
        wallet_match = re.search(r'0x[a-fA-F0-9]{40}', text)
        return wallet_match.group(0) if wallet_match else None
