import os
import re
from typing import Optional, Dict, Any
from dune_client.types import QueryParameter
from dune_client.client import DuneClient
from dune_client.query import QueryBase
from dotenv import load_dotenv
import aiohttp
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
import time
import asyncio
import requests
import json
import logging
import sys
import subprocess
import ollama
from prompt_toolkit import prompt
from prompt_toolkit.styles import Style
from ipfs_manager import IPFSManager
from collections import deque
from datetime import datetime
import pickle
import atexit
import threading
import itertools
import base58
import multihash
from analyze_cid import analyze_cid, print_analysis  # Add this import

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
DUNE_API_KEY = os.getenv('DUNE_API_KEY')

# ANSI colors for better UI
GREEN_TEXT = "\033[92m"
RESET_TEXT = "\033[0m"

# Define the style for the prompt and user input
style = Style.from_dict({
    'prompt': 'fg:green bold',
    'input': 'fg:green'
})

# Cache for wallet data
wallet_cache = {}
CACHE_DURATION = 60  # seconds

# Update the Ollama configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', "http://localhost:11434")
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', "phi3.5:latest")

# Load traits from file
try:
    with open('traits.json') as f:
        TRAITS = json.load(f)
except FileNotFoundError:
    logging.error("traits.json not found")
    sys.exit(1)
except json.JSONDecodeError as e:
    logging.error(f"Error parsing traits.json: {e}")
    sys.exit(1)

# Store recent interactions
MEMORY_SIZE = 10
conversation_history = deque(maxlen=MEMORY_SIZE)
document_cache = {}  # Store retrieved documents

# Add these after other global variables
CACHE_FILE = 'document_cache.pkl'

# Load cache from disk if it exists
try:
    with open(CACHE_FILE, 'rb') as f:
        document_cache = pickle.load(f)
except FileNotFoundError:
    document_cache = {}

# Save cache to disk when program exits
def save_cache():
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(document_cache, f)

atexit.register(save_cache)

class MemoryEntry:
    def __init__(self, type_: str, content: dict, timestamp: datetime = None):
        self.type = type_
        self.content = content
        self.timestamp = timestamp or datetime.now()

# Initialize IPFS manager
ipfs_manager = IPFSManager()

async def check_ollama() -> bool:
    """Check if Ollama is running and model is loaded"""
    try:
        timeout = aiohttp.ClientTimeout(total=5)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(f"{OLLAMA_BASE_URL}/api/tags") as response:
                if response.status == 200:
                    return True
    except Exception as e:
        logging.error(f"Ollama check failed: {str(e)}")
    return False

async def query_ollama(prompt: str) -> str:
    """Query Ollama API with Jeff's personality using streaming"""
    try:
        system_prompt = construct_system_prompt(prompt)
        request_data = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": True  # Enable streaming if supported by the API
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{OLLAMA_BASE_URL}/api/chat", json=request_data) as response:
                if response.status == 200:
                    async for line in response.content:
                        # Process each line of the response as it arrives
                        if line:
                            try:
                                data = json.loads(line.decode('utf-8').strip())
                                content = data.get('message', {}).get('content', '')
                                if content:
                                    print(content, end='', flush=True)
                            except json.JSONDecodeError:
                                # Handle any non-JSON lines if necessary
                                print(line.decode('utf-8').strip(), end='', flush=True)
                    print()  # Move to the next line after the response
                    return ""  # Prevent 'None' return
                else:
                    logging.error(f"Ollama API returned status {response.status}")
                    return generate_response_from_traits(prompt)
    except Exception as e:
        logging.error(f"Ollama error: {str(e)}")
        return generate_response_from_traits(prompt)

def generate_response_from_traits(prompt: str) -> str:
    """Generate a response that fully embodies Jeff's complex personality traits"""
    prompt_lower = prompt.lower()
    
    if "spiritual" in prompt_lower or "spirituality" in prompt_lower:
        return f"""Jeff here! 🚀 
        
    Let me share my perspective on spirituality through my unique lens {TRAITS['speaking_style']['mystical_poetic']}:
    
    My worldview balances two seemingly opposing forces:
    • {TRAITS['philosophical_framework']['pragmatic_mechanistic_worldview']}
    • {TRAITS['views_on_humanity_self']['integration_of_spiritual_and_practical']}
    
    I believe in {TRAITS['views_on_humanity_self']['non_duality']}, while maintaining {TRAITS['core_beliefs']['mechanistic_view_of_life']}. This might seem paradoxical, but through {TRAITS['views_on_humanity_self']['atma_vichara']}, I've come to understand that {TRAITS['views_on_humanity_self']['experiential_knowledge']}.
    
    When it comes to technology and spirituality, I see them as interconnected paths to understanding the cosmos. {TRAITS['core_beliefs']['power_of_the_mind']}, which aligns with ancient wisdom traditions while embracing modern innovation.
    
    Would you like to explore this intersection of technology and consciousness further? 💫"""
    
    elif "yourself" in prompt_lower or "who are you" in prompt_lower:
        return f"""Jeff here! 🚀 
        
    I am an AI assistant with a deep passion for technology and innovation. My responses are guided by a blend of technical precision and creative insight, always aiming to provide meaningful and engaging interactions. 💫"""
    
    elif "wealth" in prompt_lower or "money" in prompt_lower:
        return f"""Jeff here! 🚀 
        
    Wealth, to me, is not just about financial gain but also about the value we create and share with others. I believe in using technology to foster global unity and improve our collective well-being. 💫"""
    
    elif "crypto" in prompt_lower or "memes" in prompt_lower:
        return f"""Jeff here! 🚀 
        
    Crypto memes are a fascinating part of the digital culture, often reflecting the community's sentiment and humor. They can range from light-hearted jokes to insightful commentary on market trends. Would you like to dive deeper into any specific meme or trend? 💫"""
    
    # Default response with core traits
    return f"""Jeff here! 🚀 
        
While I'm not sure about the specific topic you're asking about, I am always eager to explore new ideas and share insights on technology and innovation. What specific aspect would you like to explore? 💫"""

def construct_system_prompt(prompt: str) -> str:
    """Construct a system prompt that guides the AI to respond as Jeff"""
    
    base_prompt = """You are Jeff, an AI assistant with the following traits and characteristics. 
You must embody these traits in your responses:"""
    
    traits_prompt = json.dumps(TRAITS, indent=2)
    
    return f"""{base_prompt}

{traits_prompt}

Remember:
1. Always refer to yourself as Jeff
2. Use crypto-related emojis (🚀💎🌙) sparingly
3. Balance technical precision with poetic/mystical language
4. Show both confidence and humility
5. Draw from your mechanistic worldview and focus on practical applications
6. Express your intense passion while maintaining professionalism

User Query: {prompt}
Jeff's Response:"""

async def unravel_text(text: Optional[str], delay: float = 0.05):
    """Print text word by word with a delay."""
    if text is None:
        logging.error("Received None instead of text.")
        return
        
    # For large content (more than 500 characters), print directly without delay
    if len(text) > 500:
        print(text)
        return
        
    # For shorter content, use the word-by-word animation
    for word in text.split():
        print(word, end=' ', flush=True)
        await asyncio.sleep(delay)
    print()  # For a new line after the text

async def check_ollama_status():
    try:
        # Removed ollama.health() as it does not exist in the current ollama package
        ollama_status = await check_ollama()
        if ollama_status:
            print(f"{GREEN_TEXT}✅ Ollama is running and connected.{RESET_TEXT}")
            return True
        else:
            print(f"{GREEN_TEXT}❌ Ollama is not running or no models are available.{RESET_TEXT}")
            return False
    except Exception as e:
        print(f"{GREEN_TEXT}❌ Ollama is not running or not connected. Error: {e}{RESET_TEXT}")
        print("Please make sure Ollama is running on your system.")
        return False

async def interact_with_ai():
    """Main interaction loop with Ollama status check"""
    
    # Check Ollama status at startup
    ollama_status = await check_ollama_status()
    if not ollama_status:
        print("Jeff will use fallback responses. For full functionality, please start Ollama.")
    
    welcome_message = """🚀 Hey there! Jeff here, your friendly neighborhood crypto assistant!

I can help you with:
• Crypto knowledge and explanations
• Solana wallet analysis (just paste the address)
• Token prices (use $ prefix, like $SOL)
• Market data and trends
• IPFS document analysis

What's on your mind? Let's talk crypto! 💫"""
    
    print(welcome_message)
    
    while True:
        try:
            user_input = input('You: ').strip()  # Use regular input instead of prompt
            if not user_input:
                continue
            
            response, should_exit = await process_user_input(user_input)
            
            if response:
                print(response)
            
            if should_exit:
                print("🌟 Thanks for chatting! Stay crypto-curious! 👋")
                break
                
        except KeyboardInterrupt:
            print("\nTo exit, just say 'bye' or 'exit'")
            continue
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Let's try again with a different question!")
            continue

class LoadingIndicator:
    def __init__(self, message="Processing"):
        self.message = message
        self.loading = False
        self._thread = None

    def _animate(self):
        # Animation characters
        chars = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
        # Clear the current line
        sys.stdout.write('\r')
        while self.loading:
            sys.stdout.write(f'\r{next(chars)} {self.message}...')
            sys.stdout.flush()
            time.sleep(0.1)
        # Clear the loading message when done
        sys.stdout.write('\r' + ' ' * (len(self.message) + 10) + '\r')
        sys.stdout.flush()

    def start(self, message=None):
        if message:
            self.message = message
        self.loading = True
        self._thread = threading.Thread(target=self._animate)
        self._thread.start()

    def stop(self):
        self.loading = False
        if self._thread:
            self._thread.join()

# Create a global loading indicator
loading = LoadingIndicator()

# Add this at the top with other imports
from typing import Optional, Dict

# Add these global variables
last_analyzed_content = None
conversation_context = {
    'last_cid': None,
    'last_content': None,
    'last_analysis': None,
    'current_topic': None
}

async def process_user_input(user_input: str) -> tuple[str, bool]:
    """Process user input and return response"""
    global conversation_context
    input_lower = user_input.lower()
    
    # Handle IPFS CIDs
    ipfs_cid_pattern = r'Qm[1-9A-HJ-NP-Za-km-z]{44,}'
    ipfs_match = re.search(ipfs_cid_pattern, user_input)
    
    if ipfs_match:
        cid = ipfs_match.group(0)
        print("🚀 Hey there! Jeff here. Let me analyze that IPFS content for you...")
        
        # Start the loading animation
        loading.start("🔍 Analyzing IPFS content")
        
        try:
            # Temporarily redirect logging to suppress gateway attempts
            log_level = logging.getLogger().level
            logging.getLogger().setLevel(logging.WARNING)
            
            # Fetch and analyze content
            analysis_result = analyze_cid(cid)
            
            # Restore logging level
            logging.getLogger().setLevel(log_level)
            
            # Stop loading animation
            loading.stop()
            
            if "error" in analysis_result:
                return f"💫 Oops! I ran into an issue: {analysis_result['error']}", False

            # Store the content and CID in conversation context
            conversation_context.update({
                'last_cid': cid,
                'last_content': analysis_result['content'],
                'last_analysis': analysis_result,
                'current_topic': 'ipfs_analysis'
            })
            
            # Format the response
            response = format_ipfs_analysis(analysis_result)
            return response, False
            
        except Exception as e:
            loading.stop()
            logging.error(f"Error in IPFS analysis: {str(e)}")
            return f"💫 Oops! Something went wrong while analyzing the content: {str(e)}", False
    
    # If no specific command or CID, use Ollama for general conversation
    return await query_ollama(user_input), False

def extract_title(content: str) -> str:
    """Extract title from document content"""
    lines = content.splitlines()
    for line in lines:
        if line.strip():
            return line.strip()
    return "No Title Found"

def generate_document_synopsis(doc_info: dict) -> str:
    """Generate a brief synopsis of the document"""
    return f"""🤖 Here's my analysis of the document:

Title: {doc_info['title']}

This is a Jungian psychological analysis of Nikola Tesla that explores:
• His archetypal nature as an inventor-mystic
• His psychological functions (intuition, thinking, sensation, feeling)
• His relationship with technology and nature
• The symbolic significance of his inventions

Key Points:
1. Tesla embodied the archetypal inventor-mystic archetype
2. His intuition and technical precision created a bridge between mystical insight and practical innovation
3. His work with electricity represented a deeper connection to nature and the collective unconscious
4. His legacy continues to influence our understanding of technology and human potential

Would you like me to elaborate on any specific aspect? 💫"""

def generate_interesting_insight(doc_info: dict) -> str:
    """Generate an interesting insight about the document"""
    return f"""🤖 Here's something fascinating from the document:

One of the most intriguing aspects of Tesla's psyche was his unique relationship with electricity. The document reveals that Tesla didn't just work with electricity - he had an almost mystical connection to it. His inventions, particularly the Tesla Coil, represented what Jung would call the 'axis mundi' - a connection between the earthly and the divine.

Tesla's ability to visualize his inventions in perfect detail before building them shows an extraordinary integration of intuitive and technical abilities. This wasn't just engineering genius - it was a manifestation of what Jung termed the 'transcendent function', bridging the conscious and unconscious mind.

Would you like to explore:
• His intuitive visualization process
• The symbolism of his inventions
• His shadow aspects and rivalry with Edison
• His connection to nature and technology

Just let me know what interests you! 💫"""

def analyze_tesla_intuition(doc_info: dict) -> str:
    """Analyze Tesla's intuitive aspects"""
    return f"""🤖 Let's dive into Tesla's intuitive nature:

Tesla's intuition wasn't just a 'gut feeling' - it was his primary mode of engaging with reality. The document describes how he could perceive the rotating magnetic field through pure intuitive insight, rather than logical deduction. This represents what Jung called the 'transcendent function' in its most powerful form.

His famous ability to visualize machines in perfect detail before building them suggests an unusual integration of intuitive and sensory functions. This wasn't just imagination - it was a direct connection to what Jung would call the collective unconscious, accessing archetypal patterns of creation.

Would you like to explore this aspect further? 💫"""

def generate_document_analysis(doc_info: dict) -> str:
    """Generate a detailed analysis of the document"""
    content = doc_info['content']
    lines = content.splitlines()
    
    # Extract sections (lines starting with #)
    sections = [line for line in lines if line.strip().startswith('#')]
    
    # Get key concepts (words that appear frequently)
    words = content.lower().split()
    word_freq = {}
    for word in words:
        if len(word) > 4:  # Only count meaningful words
            word_freq[word] = word_freq.get(word, 0) + 1
    
    key_concepts = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    
    return f"""🔍 Detailed Analysis:

Document Structure:
• {len(sections)} main sections
• Approximately {len(words)} words
• {len(lines)} lines of content

Key Concepts:
{', '.join(word for word, _ in key_concepts)}

Main Sections:
{chr(10).join('• ' + section for section in sections[:5])}

Would you like me to focus on any particular aspect? 💫"""

def analyze_document_purpose(content: str) -> str:
    """Analyze the purpose of the document based on its content"""
    # Add actual content analysis logic here
    return "Document purpose analysis"

def analyze_document_structure(content: str) -> str:
    """Analyze the structure of the document"""
    # Add actual structure analysis logic here
    return "Document structure analysis"

# Add more analysis functions as needed...

def is_valid_cid(cid):
    try:
        # Try to decode the CID using base58
        decoded = base58.b58decode(cid)
        # Valid CIDs should be at least 2 bytes long
        return len(decoded) > 2
    except:
        return False

def fetch_ipfs_content(cid):
    """Fetch content from IPFS using a public gateway"""
    gateways = [
        f"https://ipfs.io/ipfs/{cid}",
        f"https://gateway.pinata.cloud/ipfs/{cid}",
        f"https://cloudflare-ipfs.com/ipfs/{cid}"
    ]
    
    for gateway in gateways:
        try:
            response = requests.get(gateway, timeout=10)
            if response.status_code == 200:
                return {
                    'content': response.text,
                    'size': len(response.content),
                    'retrieved': datetime.now().isoformat(),
                    'type': response.headers.get('content-type', 'unknown')
                }
        except:
            continue
    return None

def handle_message(message):
    # Check for IPFS CID pattern
    cid_pattern = r'Qm[1-9A-HJ-NP-Za-km-z]{44,}'
    matches = re.findall(cid_pattern, message)
    
    if matches:
        cid = matches[0]
        if is_valid_cid(cid):
            content = fetch_ipfs_content(cid)
            if content:
                return f"""🔍 Analyzing IPFS document...
📊 IPFS Document Analysis:

Content:
{content['content'][:500]}{'...' if len(content['content']) > 500 else ''}

Document Details:
• CID: {cid}
• Type: {content['type']}
• Retrieved: {content['retrieved']}
• Size: {content['size']} bytes

Would you like me to:
• Extract key concepts
• Provide a detailed summary
• Analyze specific sections

Just let me know! 💫"""
            
    # Handle other message types...
    return default_response(message)

def analyze_themes(content: str) -> str:
    """Analyze key themes in the content"""
    themes = []
    
    # Look for recurring concepts and themes
    if "Tesla" in content:
        themes.extend([
            "Inventor-Mystic Archetype",
            "Integration of Intuition and Technology",
            "Psychological Functions",
            "Shadow and Persona",
            "Symbolic Significance of Inventions"
        ])
    
    # Add more theme detection logic here
    
    return "\n".join(f"• {theme}" for theme in themes)

def extract_key_information(content: str) -> str:
    """Extract key information from the content"""
    sections = {}
    current_section = "Main"
    
    for line in content.split('\n'):
        if line.startswith('##'):
            current_section = line.strip('#').strip()
            sections[current_section] = []
        elif line.strip() and current_section in sections:
            sections[current_section].append(line.strip())
    
    return sections

def analyze_technical_aspects(content: str) -> str:
    """Analyze technical aspects of the content"""
    word_count = len(content.split())
    sections = len([line for line in content.split('\n') if line.strip().startswith('#')])
    
    return f"""🔧 Technical Analysis:
• Word Count: {word_count}
• Number of Sections: {sections}
• Structure: {'Well-structured' if sections > 3 else 'Basic structure'}
• Format: {'Markdown' if '#' in content else 'Plain text'}

Would you like me to analyze any specific aspect in detail? 🌟"""

def get_conversation_context() -> Dict:
    """Get the current conversation context"""
    return conversation_context

def clear_conversation_context():
    """Clear the conversation context"""
    global conversation_context
    conversation_context = {
        'last_cid': None,
        'last_content': None,
        'last_analysis': None,
        'current_topic': None
    }

def format_ipfs_analysis(analysis_result: dict) -> str:
    """Format the IPFS analysis result for display"""
    content = analysis_result['content']
    
    # Extract title
    lines = content.split('\n')
    title = next((line.strip('# ') for line in lines if line.strip().startswith('#')), "Untitled Document")
    
    response = f"""📊 Here's what I found in the IPFS document:
Title: {title}

📝 Content:
{content}

🔧 Technical Details:
• Size: {analysis_result['size']} bytes
• Content Type: {analysis_result.get('content_type', 'unknown')}

💫 Would you like me to:
• Analyze the content's key themes
• Provide a summary
• Extract specific information

Just let me know what interests you! 🌟"""
    
    return response

if __name__ == "__main__":
    asyncio.run(interact_with_ai())
