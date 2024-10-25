import os
import json
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# Get the path to traits.json
traits_file_path = os.getenv('TRAITS_FILE_PATH', 'traits.json')
logging.info(f"Loading traits from: {traits_file_path}")

# Load traits.json with error handling
try:
    with open(traits_file_path) as f:
        traits = json.load(f)
    logging.info("Successfully loaded traits.json")
except FileNotFoundError:
    logging.error(f"The file {traits_file_path} was not found.")
    exit(1)
except json.JSONDecodeError as e:
    logging.error(f"Error decoding JSON: {e}")
    exit(1)
