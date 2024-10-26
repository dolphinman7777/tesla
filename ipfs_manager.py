import ipfshttpclient
import logging
import requests
import os
from typing import Optional, Dict, Any
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import json
from datetime import datetime

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

    def get_file_from_ipfs(self, cid: str) -> Dict[str, Any]:
        """Retrieve file from IPFS and return document info"""
        try:
            # First check the cache
            cache_path = os.path.join(self.cache_dir, f"{cid}.md")
            if os.path.exists(cache_path):
                with open(cache_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return {
                    'content': content,
                    'type': 'markdown',
                    'retrieved_at': datetime.now().isoformat()
                }
            
            # Updated list of reliable IPFS gateways
            gateways = [
                f"https://dweb.link/ipfs/{cid}",
                f"https://ipfs.io/ipfs/{cid}",
                f"https://gateway.ipfs.io/ipfs/{cid}",
                f"https://cloudflare-ipfs.com/ipfs/{cid}",
                f"https://w3s.link/ipfs/{cid}"
            ]
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'text/plain, text/markdown, application/json, */*'
            })
            
            for gateway in gateways:
                try:
                    logging.info(f"Trying gateway: {gateway}")
                    response = session.get(gateway, timeout=10)
                    
                    if response.status_code == 200:
                        content = response.text
                        
                        # Validate content
                        if content and len(content.strip()) > 0:
                            # Save to cache
                            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                            with open(cache_path, 'w', encoding='utf-8') as f:
                                f.write(content)
                            
                            doc_info = {
                                'content': content,
                                'type': 'markdown',
                                'retrieved_at': datetime.now().isoformat(),
                                'title': self.extract_title(content.splitlines())
                            }
                            
                            # Update index
                            self.document_index[cid] = {
                                'title': doc_info['title'],
                                'retrieved_at': doc_info['retrieved_at'],
                                'type': doc_info['type']
                            }
                            self.save_index()
                            
                            return doc_info
                except Exception as e:
                    logging.warning(f"Gateway {gateway} failed: {str(e)}")
                    continue
            
            raise Exception("Unable to retrieve document from any IPFS gateway")
            
        except Exception as e:
            logging.error(f"Error retrieving from IPFS: {str(e)}")
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
        try:
            # Split into paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            # Find the first substantial paragraph that's not a heading
            for para in paragraphs:
                if not para.startswith('#') and len(para.split()) > 10:
                    # Clean up the paragraph
                    clean_para = ' '.join(para.split())
                    # Return truncated version if too long
                    return clean_para[:300] + '...' if len(clean_para) > 300 else clean_para
            
            # Fallback to first non-empty paragraph
            for para in paragraphs:
                if para.strip():
                    return para.strip()
                    
            return "No meaningful content found"
            
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return "Error generating summary"

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
        # Use reliable gateways
        self.gateways = [
            "https://ipfs.io/ipfs/",
            "https://dweb.link/ipfs/",
            "https://cf-ipfs.com/ipfs/",
            "https://gateway.pinata.cloud/ipfs/"
        ]
        
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Accept': 'text/plain, text/markdown, */*'
        }
        
        for gateway in self.gateways:
            try:
                url = f"{gateway}{cid}"
                logging.info(f"🔍 Trying gateway: {gateway}")
                
                response = requests.get(
                    url, 
                    headers=headers,
                    timeout=10,
                    verify=True,
                    allow_redirects=True
                )
                
                if response.status_code == 200:
                    content = response.text
                    
                    # Validate we got actual content
                    if len(content.strip()) > 20 and 'Gateway Checker' not in content:
                        doc_info = {
                            'cid': cid,
                            'content': content,
                            'title': self.extract_title(content.splitlines()),
                            'retrieved_from': gateway,
                            'retrieved_at': datetime.now().isoformat(),
                            'type': self.detect_document_type(content)
                        }
                        
                        # Cache valid content
                        self.save_to_cache(cid, doc_info)
                        self.current_document = doc_info
                        return doc_info
                        
            except Exception as e:
                logging.warning(f"Failed to retrieve from {gateway}: {str(e)}")
                continue
        
        raise Exception("Could not retrieve valid content from any gateway")

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

    def create_basic_summary(self, content: str) -> str:
        """Create a basic summary of the content"""
        try:
            # Get first non-empty paragraph
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if paragraphs:
                first_para = paragraphs[0]
                # Truncate if too long
                return first_para[:300] + "..." if len(first_para) > 300 else first_para
            return "No content available for summary"
        except Exception as e:
            logging.error(f"Error creating summary: {e}")
            return "Error creating summary"

    def save_to_cache(self, cid: str, doc_info: dict):
        """Save document to cache"""
        try:
            # Save content file
            cache_path = os.path.join(self.cache_dir, f"{cid}.txt")
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(doc_info['content'])
            
            # Update index
            self.document_index[cid] = {
                'title': doc_info['title'],
                'retrieved_at': doc_info['retrieved_at'],
                'type': doc_info['type']
            }
            self.save_index()
            
        except Exception as e:
            logging.error(f"Error saving to cache: {e}")

    def create_summary(self, paragraphs: list) -> str:
        """Create a summary from paragraphs"""
        for para in paragraphs:
            # Find first substantial paragraph
            if len(para.split()) > 5 and not para.startswith('#'):
                return para[:300] + '...' if len(para) > 300 else para
        return "No meaningful content found"

    def analyze_content(self, content: str) -> str:
        """Analyze content and create a meaningful summary"""
        try:
            # Split into paragraphs
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            
            # Get meaningful content
            meaningful_content = []
            for para in paragraphs:
                # Skip headers and short lines
                if not para.startswith('#') and len(para.split()) > 5:
                    meaningful_content.append(para)
            
            if meaningful_content:
                # Get the first substantial paragraph
                summary = meaningful_content[0]
                # Truncate if too long
                if len(summary) > 300:
                    summary = summary[:300] + "..."
                return summary
            
            return "No meaningful content found"
            
        except Exception as e:
            logging.error(f"Error analyzing content: {e}")
            return "Error analyzing content"

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

