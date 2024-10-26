import requests
from datetime import datetime
import base58
import multihash
import logging
import re

logging.basicConfig(level=logging.INFO)

def is_ipfs_v1(cid):
    """Check if CID is IPFS v1 format"""
    return cid.startswith('baf')

def analyze_cid(cid):
    """Analyze an IPFS CID and fetch its content"""
    try:
        # List of popular IPFS gateways with different formats
        gateways = [
            f"https://ipfs.io/ipfs/{cid}",
            f"https://dweb.link/ipfs/{cid}",
            f"https://gateway.pinata.cloud/ipfs/{cid}",
            f"https://{cid}.ipfs.dweb.link",
            f"https://cloudflare-ipfs.com/ipfs/{cid}",
            f"https://gateway.ipfs.io/ipfs/{cid}"
        ]
        
        # Try to fetch content from different gateways
        content = None
        used_gateway = None
        response = None
        
        for gateway in gateways:
            try:
                logging.info(f"Trying gateway: {gateway}")
                response = requests.get(gateway, timeout=10, 
                                     headers={'Accept': 'text/plain,text/markdown,*/*'})
                if response.status_code == 200:
                    content = response.text
                    used_gateway = gateway
                    logging.info(f"Successfully retrieved content from {gateway}")
                    break
            except requests.RequestException as e:
                logging.warning(f"Failed to fetch from {gateway}: {str(e)}")
                continue

        if not content:
            logging.error("Could not retrieve content from any gateway")
            return {
                "error": "Could not retrieve content from any gateway",
                "cid": cid
            }

        # Decode CID information
        cid_info = {}
        try:
            if is_ipfs_v1(cid):
                # Handle v1 CID differently if needed
                cid_info = {
                    "version": "1",
                    "encoding": "base32",
                    "cid": cid
                }
            else:
                decoded = base58.b58decode(cid)
                mh = multihash.decode(decoded)
                cid_info = {
                    "version": "0",
                    "hash_function": mh.name,
                    "hash_length": mh.length,
                    "digest": mh.digest.hex()
                }
        except Exception as e:
            logging.error(f"CID decode error: {str(e)}")
            cid_info = {"error": f"Could not decode CID: {str(e)}"}

        # Analyze the actual content
        content_analysis = {
            "cid": cid,
            "content": content,
            "retrieved": datetime.now().isoformat(),
            "size": len(content.encode('utf-8')),
            "cid_details": cid_info,
            "gateway_used": used_gateway,
            "content_type": response.headers.get('content-type', 'text/plain') if response else 'unknown',
        }

        return content_analysis

    except Exception as e:
        logging.error(f"General error: {str(e)}")
        return {
            "error": f"Error analyzing CID: {str(e)}",
            "cid": cid
        }

def print_analysis(result):
    """Print the analysis results in a formatted way"""
    print("🔍 IPFS Content Analysis:")
    print("-" * 50)
    print(f"CID: {result['cid']}")
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return

    print(f"\n📝 Content:")
    print(result['content'])
    
    print(f"\n📊 Technical Details:")
    print(f"• Retrieved: {result['retrieved']}")
    print(f"• Size: {result['size']} bytes")
    print(f"• Content Type: {result.get('content_type', 'unknown')}")
    
    if 'cid_details' in result and isinstance(result['cid_details'], dict):
        print("\n🔐 CID Information:")
        for key, value in result['cid_details'].items():
            print(f"• {key}: {value}")

if __name__ == "__main__":
    # Example usage
    test_cid = "QmcQgPjXUvmitBcd3BHjNyEk2HRe7D4YU5smFnLMNi1WW7"
    analysis = analyze_cid(test_cid)
    print_analysis(analysis)
