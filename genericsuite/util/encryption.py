"""
Cryptography module for encrypting and decrypting strings.
"""
from cryptography.fernet import Fernet, InvalidToken


def encrypt_string(seed: str, string: str) -> str:
    """
    Encrypt a string with a seed string.

    Args:
        seed (str): Seed string.
        string (str): String to be encrypted.

    Returns:
        str: Encrypted string.
    """
    encrypted = Fernet(seed).encrypt(string.encode())
    return encrypted.decode()


def decrypt_string(seed: str, encrypted_str: str) -> str:
    """
    Decrypt an encrypted string with a seed string.

    Args:
        seed (str): Seed string.
        encrypted_str (str): Encrypted string.

    Returns:
        str: Decrypted string.
    """
    encrypted = encrypted_str.encode()
    try:
        decrypted = Fernet(seed).decrypt(encrypted)
    except InvalidToken:
        return None
    return decrypted.decode()
