"""Prefixed, Base62-encoded random identifiers, like ``sub_4vD8m0fQ2kZ7xT1yN9bR3a``."""

import secrets

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
_LENGTH = 22


def new_id(prefix: str) -> str:
    """Return ``<prefix>_`` followed by 128 random bits in Base62."""
    number = secrets.randbits(128)
    digits = []
    for _ in range(_LENGTH):
        number, remainder = divmod(number, len(_ALPHABET))
        digits.append(_ALPHABET[remainder])
    return f"{prefix}_{''.join(reversed(digits))}"
