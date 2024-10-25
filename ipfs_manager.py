import ipfshttpclient
import logging
import requests
import os
from typing import Optional
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

def connect_to_ipfs():
    """Connect to the local IPFS node."""
    try:
        client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
        logging.info("Connected to IPFS node.")
        return client
    except Exception as e:
        logging.error(f"Failed to connect to IPFS: {e}")
        return None

def add_file_to_ipfs(file_path: str) -> str:
    """Add a file to IPFS and return its CID."""
    try:
        # For now, we'll just log that this functionality requires a local node
        logging.warning("Adding files to IPFS requires a local node. Please use IPFS Desktop or command line tools.")
        return ""
    except Exception as e:
        logging.error(f"Failed to add file to IPFS: {e}")
        return ""

def create_session():
    """Create a requests session with retries and timeouts"""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.1,
        status_forcelist=[500, 502, 503, 504]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_file_from_ipfs(cid: str, output_path: str) -> Optional[str]:
    """Retrieve a file from IPFS using its CID."""
    # Use multiple gateways for redundancy
    gateways = [
        "https://ipfs.io/ipfs/",
        "https://cloudflare-ipfs.com/ipfs/",
        "https://w3s.link/ipfs/",
        "https://gateway.pinata.cloud/ipfs/"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/plain, application/json, */*'
    }
    
    for gateway in gateways:
        try:
            url = f"{gateway}{cid}"
            logging.info(f"Trying gateway: {gateway}")
            
            response = requests.get(
                url, 
                headers=headers,
                timeout=10,
                verify=True
            )
            
            if response.status_code == 200:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
                
                # Write the content to file
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                
                logging.info(f"Successfully retrieved file from {gateway}")
                return output_path
                
        except Exception as e:
            logging.warning(f"Failed to retrieve from {gateway}: {str(e)}")
            continue
    
    raise Exception("Failed to retrieve file from all IPFS gateways")
