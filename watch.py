import asyncio
from watchfiles import arun_process
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the path to traits.json from environment variables
traits_file_path = os.getenv('TRAITS_FILE_PATH', 'traits.json')

# Load character traits with error handling
try:
    with open(traits_file_path) as f:
        traits = json.load(f)
except FileNotFoundError:
    print(f"Error: The file {traits_file_path} was not found.")
    exit(1)
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
    exit(1)

async def run_script():
    await arun_process('.', target='python3 web.py')  # Watch the current directory

if __name__ == '__main__':
    asyncio.run(run_script())
