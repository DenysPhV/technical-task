import os

API_KEY = os.getenv('API_KEY', '')

def get_api_key():
    """
    Return the API key.
    """
    if not API_KEY:
        raise ValueError("No API key available")
    return API_KEY