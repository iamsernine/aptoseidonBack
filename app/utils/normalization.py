import hashlib
import re
from urllib.parse import urlparse

def normalize_input(input_str: str) -> str:
    """
    Canonicalizes input:
    - URL: Strips scheme, www, and query params. Lowercase.
    - Address: Lowercase, keep 0x.
    - Name: Lowercase, trimmed.
    """
    input_str = input_str.strip().lower()
    
    # Check if URL
    if input_str.startswith("http") or "://" in input_str:
        try:
            parsed = urlparse(input_str)
            # Return netloc + path, stripped of trailing slash
            clean = f"{parsed.netloc}{parsed.path}"
            return clean.replace("www.", "").rstrip("/")
        except:
            pass
            
    return input_str

def generate_fingerprint(input_str: str, extra_data: str = "") -> str:
    """
    Generates a unique SHA256 hash for the project.
    """
    clean_input = normalize_input(input_str)
    payload = f"{clean_input}|{extra_data}"
    return hashlib.sha256(payload.encode()).hexdigest()
