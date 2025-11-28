import hmac
import hashlib

def verify_webhook_signature(body: bytes, signature: str, secret: str) -> bool:
    if not secret:
        # If no secret configured, allow (dev mode)
        return True
    mac = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(mac, signature)
