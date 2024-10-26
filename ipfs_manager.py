import ipfshttpclient
import logging
import requests
import os
from typing import Optional
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json

class IPFSManager:
    def __init__(self):
        self.gateways = [
            "https://gateway.pinata.cloud/ipfs/",
            "https://cloudflare-ipfs.com/ipfs/",
            "https://ipfs.io/ipfs/",
            "https://w3s.link/ipfs/"
        ]
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/plain, application/json, */*'
        }
        
        # Create cache directory if it doesn't exist
        self.cache_dir = 'ipfs_cache'
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load document index
        self.index_file = os.path.join(self.cache_dir, 'document_index.json')
        self.document_index = self.load_index()
        
        # Track document history
        self.document_history = []
        self.current_document = None

    def load_index(self) -> dict:
        """Load the document index from file"""
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logging.error(f"Error loading index: {e}")
        return {}

    def save_index(self):
        """Save the document index to file"""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self.document_index, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving index: {e}")

    def get_file_from_ipfs(self, cid: str) -> Optional[dict]:
        """Retrieve a file from IPFS using its CID"""
        try:
            # Check cache first
            doc_info = self.get_from_cache(cid)
            if doc_info:
                self.update_document_context(doc_info)
                return doc_info

            # Try retrieving from IPFS
            doc_info = self.retrieve_from_ipfs(cid)
            if doc_info:
                self.update_document_context(doc_info)
                return doc_info

        except Exception as e:
            logging.error(f"Error retrieving document: {e}")
            raise

    def update_document_context(self, doc_info: dict):
        """Update the document context"""
        self.current_document = doc_info
        if doc_info not in self.document_history:
            self.document_history.append(doc_info)
        if len(self.document_history) > 10:  # Keep last 10 documents
            self.document_history.pop(0)

    def get_document_context(self) -> dict:
        """Get current document context"""
        return {
            'current': self.current_document,
            'history': self.document_history,
            'total_documents': len(self.document_history)
        }

    def analyze_document(self, doc_info: dict) -> dict:
        """Analyze document content and type"""
        content = doc_info['content']
        lines = content.splitlines()
        
        # Basic document analysis
        analysis = {
            'title': self.extract_title(lines),
            'type': self.detect_document_type(content),
            'sections': self.extract_sections(lines),
            'summary': self.generate_summary(content)
        }
        
        return {**doc_info, 'analysis': analysis}

    def detect_document_type(self, content: str) -> str:
        """Detect the type of document based on content"""
        if content.startswith('# '):
            return 'markdown'
        elif '<html' in content.lower():
            return 'html'
        elif '{' in content and '}' in content:
            try:
                json.loads(content)
                return 'json'
            except:
                pass
        return 'text'

    def extract_sections(self, lines: list) -> list:
        """Extract main sections from the document"""
        sections = []
        current_section = None
        
        for line in lines:
            if line.startswith('#'):
                if current_section:
                    sections.append(current_section)
                current_section = {'title': line.lstrip('#').strip(), 'content': []}
            elif current_section:
                current_section['content'].append(line)
                
        if current_section:
            sections.append(current_section)
            
        return sections

    def generate_summary(self, content: str) -> str:
        """Generate a meaningful summary of the document"""
        lines = content.splitlines()
        paragraphs = []
        current_para = []
        
        for line in lines:
            if line.strip():
                current_para.append(line.strip())
            elif current_para:
                paragraphs.append(' '.join(current_para))
                current_para = []
        
        if current_para:
            paragraphs.append(' '.join(current_para))
        
        # Get first meaningful paragraph
        for para in paragraphs:
            if len(para) > 50 and not para.startswith('#'):
                return para[:300] + "..." if len(para) > 300 else para
            
        return paragraphs[0] if paragraphs else "No content available"

    def get_from_cache(self, cid: str) -> Optional[dict]:
        """Get a document from cache"""
        cached_path = os.path.join(self.cache_dir, f"{cid}.md")
        if os.path.exists(cached_path):
            try:
                with open(cached_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    'cid': cid,
                    'content': content,
                    'cached': True,
                    **self.document_index[cid]
                }
            except Exception as e:
                logging.warning(f"Error reading cached file: {e}")

    def retrieve_from_ipfs(self, cid: str) -> Optional[dict]:
        """Retrieve a file from IPFS"""
        # Updated gateway list with most reliable gateways
        self.gateways = [
            "https://dweb.link/ipfs/",
            "https://ipfs.io/ipfs/",
            "https://gateway.ipfs.io/ipfs/",
            "https://cf-ipfs.com/ipfs/"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/plain, text/markdown, */*',
            'Connection': 'close'
        }
        
        for gateway in self.gateways:
            try:
                url = f"{gateway}{cid}"
                logging.info(f"Trying gateway: {gateway}")
                
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(
                    url, 
                    timeout=(5, 15),  # (connect timeout, read timeout)
                    verify=True,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Validate content
                    if self.is_valid_document(content):
                        # Save to cache
                        cache_path = os.path.join(self.cache_dir, f"{cid}.md")
                        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                        
                        with open(cache_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        
                        # Extract title and update index
                        lines = content.splitlines()
                        title = self.extract_title(lines)
                        
                        # Get a proper summary
                        summary = self.generate_summary(content)
                        
                        doc_info = {
                            'title': title,
                            'content': content,
                            'retrieved_from': gateway,
                            'type': self.detect_document_type(content),
                            'summary': summary,
                            'length': len(lines),
                            'sections': self.extract_sections(lines)
                        }
                        
                        self.document_index[cid] = doc_info
                        self.save_index()
                        
                        logging.info(f"Successfully retrieved document from {gateway}")
                        return doc_info
                
            except Exception as e:
                logging.warning(f"Error with {gateway}: {str(e)}")
                continue
            finally:
                session.close()
        
        raise Exception("Failed to retrieve valid document from all IPFS gateways")

    def extract_title(self, lines: list) -> str:
        """Extract title from document lines"""
        for line in lines:
            line = line.strip()
            if line:
                # Remove markdown heading symbols
                return line.lstrip('#').strip()
        return "No Title Found"

    def is_valid_document(self, content: str) -> bool:
        """Validate that we got a real document and not a gateway page"""
        # Check for common gateway page indicators
        invalid_indicators = [
            "Gateway Checker",
            "Error 404",
            "Not Found",
            "Gateway Time-out",
            "Bad Gateway"
        ]
        
        # Check content length and quality
        lines = content.splitlines()
        if len(lines) < 3:
            return False
        
        # Check for invalid indicators
        for indicator in invalid_indicators:
            if indicator in content:
                return False
            
        # Check for meaningful content
        meaningful_lines = [line for line in lines if len(line.strip()) > 20]
        if len(meaningful_lines) < 2:
            return False
        
        return True

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
