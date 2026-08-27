import secrets

def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)