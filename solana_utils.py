import re

def is_solana_address(text):
    """
    Validate if a given text is a valid Solana address.
    Solana addresses are 44 characters long and Base58 encoded.
    """
    if not text:
        return False
    return bool(re.match(r'^[1-9A-HJ-NP-Za-km-z]{44}$', text))
