"""Password hashes shared by the desktop and HTTP modes."""
import hashlib
import hmac
import secrets


def _derive(password, salt):
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)


def hash_password(password):
    salt = secrets.token_bytes(16)
    return f"scrypt${salt.hex()}${_derive(password, salt).hex()}"


def verify_password(password, stored):
    if not stored.startswith("scrypt$"):
        legacy = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(legacy, stored)
    try:
        _, salt, digest = stored.split("$")
        return hmac.compare_digest(_derive(password, bytes.fromhex(salt)), bytes.fromhex(digest))
    except ValueError:
        return False
