# Add this method to the CryptoAssistant class
from config.ai_persona import TRAITS
from ipfs_manager import add_file_to_ipfs, get_file_from_ipfs
import re

def format_response(self, data: dict, intent: QueryIntent) -> str:
    token = intent.parameters.get('token_symbol', 'Unknown')
    
    if intent.query_type == 'token_metrics':
        response = f"""📊 Analysis for {token}:
💰 Price: ${float(data['price']):.4f}
📈 24h Volume: ${float(data['volume_24h']):,.2f}
💎 Market Cap: ${float(data['market_cap']):,.2f}
👥 Holders: {int(data['holder_count']):,}
🔄 24h Transactions: {int(data['transactions_24h']):,}"""
        
    elif intent.query_type == 'token_price_prediction':
        confidence = data.get('prediction_confidence', 0.5)
        direction = "🟢 Bullish" if data.get('prediction_direction') == 'up' else "🔴 Bearish"
        response = f"""🔮 Price Prediction for {token}:
{direction} (Confidence: {confidence:.1%})
Expected Range: ${float(data['price_lower']):,.2f} - ${float(data['price_upper']):,.2f}
Timeframe: {intent.time_period}"""
        
    elif intent.query_type == 'token_sentiment':
        sentiment_score = float(data.get('sentiment_score', 0))
        sentiment = "Very Positive 🚀" if sentiment_score > 0.6 else \
                   "Positive 📈" if sentiment_score > 0.2 else \
                   "Neutral ↔️" if sentiment_score > -0.2 else \
                   "Negative 📉" if sentiment_score > -0.6 else "Very Negative 📉"
        response = f"""📊 Social Sentiment for {token}:
Overall: {sentiment}
Social Volume: {int(data.get('social_volume', 0)):,} mentions
Trending: {'🔥' if data.get('is_trending') else '❄️'}"""
        
    elif intent.query_type == 'wallet_analysis':
        wallet = intent.parameters.get('wallet_address', 'Unknown')
        response = f"""🔍 Wallet Analysis for {token}:
👛 Address: {wallet[:6]}...{wallet[-4:]}
💰 Balance: {float(data['wallet_balance']):.4f} {token} (${float(data['wallet_balance_usd']):,.2f})
📊 Activity Level: {data['activity_level']}
🏷️ Category: {data['wallet_category']}

30-Day Activity:
📥 Receives: {int(data['total_receives']):,}
📤 Sends: {int(data['total_sends']):,}
🔄 Total Transactions: {int(data['total_transactions']):,}

Token Metrics:
💎 Market Cap: ${float(data['market_cap']):,.2f}
📈 24h Volume: ${float(data['volume_24h']):,.2f}
👥 Total Holders: {int(data['total_holders']):,}"""
        
    # Add more formatting options for other query types...
    
    # Incorporate relevant traits
    for category, traits in TRAITS.items():
        for trait, description in traits.items():
            if trait in intent.parameters or category.lower() in intent.query_type:
                response += f"\n\nAs someone who {description}, I'd like to add: ..."
    
    return response

async def process_user_input(user_input: str) -> tuple[str, bool]:
    """Process user input and return response"""
    input_lower = user_input.lower()
    
    # Handle basic commands first
    if input_lower in ['exit', 'quit', 'bye']:
        return "Goodbye! Have a great day!", True
    
    # Handle IPFS CIDs
    ipfs_cid_pattern = r'Qm[1-9A-HJ-NP-Za-km-z]{44,}'
    ipfs_match = re.search(ipfs_cid_pattern, user_input)
    if ipfs_match:
        cid = ipfs_match.group(0)
        try:
            output_path = f'retrieved_document_{cid[:10]}.md'
            get_file_from_ipfs(cid, output_path)
            
            with open(output_path, 'r') as file:
                content = file.read()
                title = extract_title(content)
                return f"📄 Document retrieved from IPFS!\nTitle: {title}\nContent:\n{content}", False
        except Exception as e:
            return f"❌ Error retrieving document from IPFS: {e}", False
            
    # Only proceed to Solana processing if no IPFS match
    solana_match = re.search(r'([1-9A-HJ-NP-Za-km-z]{44})', user_input)
    if solana_match and not ipfs_match:  # Add this check
        try:
            wallet = solana_match.group(1)
            force_refresh = 'refresh' in input_lower
            data = await get_solana_data(wallet, force_refresh)
            # ... rest of the Solana wallet processing ...
        except Exception as e:
            return f"❌ Error processing Solana wallet: {e}", False
    
    # For general queries, use Ollama
    response = await query_ollama(user_input)
    return response, False

def extract_title(content: str) -> str:
    """Extract title from document content"""
    lines = content.splitlines()
    # Skip empty lines and get the first non-empty line as title
    for line in lines:
        if line.strip():
            return line.strip()
    return "No Title Found"

def main():
    # Example usage
    cid = 'your_file_cid_here'
    output_path = 'path/to/save/document.txt'
    get_file_from_ipfs(cid, output_path)

def test_ipfs_integration():
    # Path to the test file
    file_path = 'test_document.txt'
    
    # Add the file to IPFS
    cid = add_file_to_ipfs(file_path)
    if cid:
        print(f"File added to IPFS with CID: {cid}")
        
        # Retrieve the file from IPFS
        output_path = 'retrieved_document.txt'
        get_file_from_ipfs(cid, output_path)
        print(f"File retrieved from IPFS and saved to {output_path}")

def retrieve_file_from_ipfs():
    # Replace 'your_file_cid_here' with the actual CID of your uploaded file
    cid = 'QmSstMLitD1FwFSkvd1r6cEELCpKmjVqH7b4ynRXqWQGBT'
    output_path = 'retrieved_tesla_jungian_analysis.md'
    
    # Retrieve the file from IPFS
    get_file_from_ipfs(cid, output_path)
    print(f"File retrieved from IPFS and saved to {output_path}")

def interact_with_document(cid: str):
    # Define the output path for the retrieved document
    output_path = 'retrieved_document.md'
    
    # Retrieve the file from IPFS
    get_file_from_ipfs(cid, output_path)
    print(f"File retrieved from IPFS and saved to {output_path}")
    
    # Simulate Jeff interacting with the document
    try:
        with open(output_path, 'r') as file:
            content = file.read()
            print("Jeff is processing the document...")
            # Example: Extract the title from the document
            title = extract_title(content)
            print(f"Document Title: {title}")
    except FileNotFoundError:
        print("Error: File not found.")
    except Exception as e:
        print(f"An error occurred while processing the document: {e}")

if __name__ == "__main__":
    main()
    test_ipfs_integration()
    retrieve_file_from_ipfs()
    # Replace with your actual CID
    document_cid = 'QmcQgPjXUvmitBcd3BHjNyEk2HRe7D4YU5smFnLMNi1WW7'
    interact_with_document(document_cid)
