import sys
import httpx
from bs4 import BeautifulSoup
import subprocess
from functools import lru_cache
import asyncio
import concurrent.futures
import json
import os
import base64

# File to store memory
MEMORY_FILE = 'memory.json'

# ANSI escape code for green text
GREEN_TEXT = "\033[92m"
RESET_TEXT = "\033[0m"

# Twitter API credentials
BEARER_TOKEN = 'AAAAAAAAAAAAAAAAAAAAACFhwgEAAAAAPH9g%2FzQ9c8mS5OGCpB3JtibFMy0%3DCdsBCwhI6uAI4io851EORIxh0JcO0ZsfREmTVhTE9OzCj3ysZ8'

# Load memory from file
def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    return []

# Save memory to file
def save_memory(memory):
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f)

# Load existing memory
memory = load_memory()

@lru_cache(maxsize=100)
async def scrape_website(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                paragraphs = [p.text for p in soup.find_all('p')]
                prompt = " ".join(paragraphs[:5])
                return prompt
            elif response.status_code == 404:
                return "The page was not found (404 error). Please check the URL."
            else:
                return f"Failed to retrieve data. Status code: {response.status_code}"
        except httpx.RequestError as e:
            return f"An error occurred while requesting the page: {str(e)}"

async def fetch_pair_info(base, quote):
    search_url = f"https://api.dexscreener.com/latest/dex/search/?q={base}/{quote}"
    async with httpx.AsyncClient() as client:
        try:
            search_response = await client.get(search_url)
            if search_response.status_code == 200:
                search_data = search_response.json()
                if search_data['pairs']:
                    pair = search_data['pairs'][0]
                    pair_address = pair['pairAddress']
                    chain_id = pair['chainId']
                    
                    pair_url = f"https://api.dexscreener.com/latest/dex/pairs/{chain_id}/{pair_address}"
                    pair_response = await client.get(pair_url)
                    if pair_response.status_code == 200:
                        pair_info = pair_response.json()
                        price_usd = pair_info.get('pair', {}).get('priceUsd', 'N/A')
                        liquidity_usd = pair_info.get('pair', {}).get('liquidity', {}).get('usd', 'N/A')
                        volume_24h = pair_info.get('pair', {}).get('volume', {}).get('h24', 'N/A')
                        url = pair_info.get('pair', {}).get('url', 'N/A')
                        return (f"Pair {base}/{quote}:\n"
                                f"Price: {price_usd} USD\n"
                                f"Liquidity: {liquidity_usd} USD\n"
                                f"24h Volume: {volume_24h} USD\n"
                                f"More Info: {url}")
                    else:
                        return f"Failed to retrieve detailed information for trading pair {base}/{quote}."
                else:
                    return f"No trading pairs found for {base}/{quote}."
            else:
                return f"Failed to search for trading pair {base}/{quote}."
        except Exception as e:
            return f"An error occurred while fetching data: {str(e)}"

def run_subprocess(prompt):
    return subprocess.run(['ollama', 'run', 'phi3', prompt], capture_output=True, text=True).stdout

async def run_ollama(prompt):
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, run_subprocess, prompt)
    return result

async def fetch_recent_tweets(username, count=1):
    user_id = await fetch_user_id(username)
    if not user_id:
        return [f"Error: User {username} not found."]
    
    # Get fresh OAuth token
    access_token = await get_oauth_token()
    if not access_token:
        return ["Error: Could not authenticate with Twitter API"]
    
    url = f"https://api.twitter.com/2/users/{user_id}/tweets"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    params = {
        "max_results": count,
        "tweet.fields": "created_at,text"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            tweets = response.json()
            return [f"{tweet['text']}" for tweet in tweets['data'][:count]]
        else:
            return [f"Error: {response.status_code} - {response.text}"]

async def interact_with_ai():
    global memory
    print("Welcome to the AI interaction session. Type 'exit' to quit or 'reset' to clear memory.")
    while True:
        user_input = input(f"{GREEN_TEXT}You: {RESET_TEXT}")
        user_input_lower = user_input.lower()
        
        if user_input_lower == 'exit':
            break
        elif user_input_lower == 'reset':
            memory = []
            print("Memory has been reset.")
        # Fix the tweet query condition
        elif ("tweet" in user_input_lower and 
              ("last" in user_input_lower or 
               "latest" in user_input_lower or 
               any(word in user_input_lower for word in ["what's", "whats", "what is"]))):
            
            # Extract username, default to elonmusk
            username = "elonmusk"  # default
            if "from" in user_input_lower:
                username = user_input_lower.split("from")[-1].strip()
            elif "@" in user_input:
                username = user_input.split("@")[-1].split()[0].strip()
            
            # Remove @ and any possessive 's if present
            username = username.replace("@", "").replace("'s", "").strip()
            
            tweets = await fetch_recent_tweets(username, count=1)
            print(f"AI: Latest tweet from @{username}:")
            for tweet in tweets:
                print(tweet)
        elif user_input.startswith("tweets "):
            username = user_input.split(" ")[1]
            tweets = await fetch_recent_tweets(username, count=5)
            print(f"AI: Recent tweets from @{username}:")
            for tweet in tweets:
                print(tweet)
        elif user_input.startswith("http"):
            prompt = await scrape_website(user_input)
            if prompt != "Failed to retrieve data.":
                analysis = await run_ollama(prompt)
                memory.append((user_input, analysis))
                print("AI Analysis:", analysis)
            else:
                print(prompt)
        elif "/" in user_input:
            base, quote = user_input.split("/")
            pair_info = await fetch_pair_info(base.strip(), quote.strip())
            print("AI:", pair_info)
        elif "$" in user_input:
            crypto_name = user_input.split("$")[1].strip()
            crypto_info = await fetch_crypto_info(crypto_name)
            print("AI:", crypto_info)
        else:
            # Handle general conversation using Ollama
            response = await run_ollama(user_input)
            memory.append((user_input, response))
            print("AI:", response)

    save_memory(memory)

async def fetch_user_id(username):
    # Get fresh OAuth token
    access_token = await get_oauth_token()
    if not access_token:
        return None
        
    url = f"https://api.twitter.com/2/users/by/username/{username}"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            return user_data['data']['id']
        else:
            print(f"Error fetching user ID: {response.status_code} - {response.text}")
            return None

async def get_oauth_token():
    auth_url = "https://api.twitter.com/oauth2/token"
    auth_data = {
        'grant_type': 'client_credentials'
    }
    auth_header = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode('ascii')
    ).decode('ascii')
    
    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(auth_url, data=auth_data, headers=headers)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Error getting OAuth token: {response.status_code} - {response.text}")
            return None

if __name__ == "__main__":
    asyncio.run(interact_with_ai())
