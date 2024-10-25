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
from ipfs_manager import get_file_from_ipfs

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

What's on your mind? Let's talk crypto! 💫"""
    
    await unravel_text(welcome_message)
    
    while True:
        try:
            user_input = await asyncio.get_event_loop().run_in_executor(None, lambda: prompt('You: ', style=style).strip())
            if not user_input:
                continue  # Ignore empty inputs
            response, should_exit = await process_user_input(user_input)
            if response:
                await unravel_text(response)
            
            if should_exit:
                await unravel_text("🌟 Thanks for chatting! Stay crypto-curious! 👋")
                break
                
        except KeyboardInterrupt:
            print("\nTo exit, just say 'bye' or 'exit'")
            continue
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            print("Let's try again with a different question!")
            continue

async def process_user_input(user_input: str) -> tuple[str, bool]:
    """Process user input and return response"""
    input_lower = user_input.lower()
    
    # Handle basic commands first
    if input_lower in ['exit', 'quit', 'bye']:
        return "Goodbye! Have a great day!", True
    
    # Handle IPFS CIDs first - before any other processing
    ipfs_cid_pattern = r'Qm[1-9A-HJ-NP-Za-km-z]{44,}'
    ipfs_match = re.search(ipfs_cid_pattern, user_input)
    if ipfs_match:
        cid = ipfs_match.group(0)
        try:
            output_path = f'retrieved_document_{cid[:10]}.md'
            # Get the file from IPFS
            get_file_from_ipfs(cid, output_path)
            
            # Read the file content
            try:
                with open(output_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    # Extract title from content
                    title = content.splitlines()[0] if content else "No Title Found"
                    
                    # Print directly instead of using unravel_text
                    print(f"\n📄 IPFS Document Retrieved!\n")
                    print(f"Title: {title}\n")
                    print("Content:")
                    print(content)
                    print("\n")
                    
                    # Return empty string to avoid unravel_text
                    return "", False
                    
            except Exception as e:
                return f"❌ Error reading document: {str(e)}", False
                
        except Exception as e:
            return f"❌ Error retrieving document from IPFS: {str(e)}", False
    
    # Handle other cases...
    # ... rest of the function remains the same ...

def extract_title(content: str) -> str:
    """Extract title from document content"""
    lines = content.splitlines()
    for line in lines:
        if line.strip():
            return line.strip()
    return "No Title Found"

if __name__ == "__main__":
    asyncio.run(interact_with_ai())
