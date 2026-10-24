"""Wachtwoorden en pincodes veilig opslaan: pbkdf2-sha256 met salt.

Het formaat bewaart de methode en de parameters mee ("pbkdf2_sha256$600000$salt$hash"),
zodat een sterkere methode later kan zonder dat iemand opnieuw moet beginnen.
"""

import base64
import hashlib
import hmac
import os

METHODE = "pbkdf2_sha256"
ITERATIES = 600_000


def _b64(b):
    return base64.b64encode(b).decode("ascii")


def maak(wachtwoord, iteraties=None):
    iteraties = iteraties or ITERATIES
    salt = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", wachtwoord.encode("utf-8"), salt, iteraties)
    return f"{METHODE}${iteraties}${_b64(salt)}${_b64(h)}"


def controleer(wachtwoord, opgeslagen):
    try:
        methode, iteraties, salt, h = opgeslagen.split("$")
        if methode != METHODE:
            return False
        nieuw = hashlib.pbkdf2_hmac("sha256", wachtwoord.encode("utf-8"), base64.b64decode(salt), int(iteraties))
        return hmac.compare_digest(nieuw, base64.b64decode(h))
    except (ValueError, AttributeError):
        return False


def verouderd(opgeslagen):
    """True als het met een zwakkere instelling gemaakt werd dan wat we nu gebruiken."""
    try:
        methode, iteraties, _, _ = opgeslagen.split("$")
        return methode != METHODE or int(iteraties) < ITERATIES
    except (ValueError, AttributeError):
        return True
