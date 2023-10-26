#!/usr/bin/env python3

from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey


def decrypt_pubkey(pubkey: RSAPublicKey) -> RSAPrivateKey:
    """
    Derives a private RSA key from the public key.

    RSA keys have the satisfy the following equation:
    m^(e*d) ≡ m (mod n)
    Here m is the message, e and n are known are d is to be found.
    """
    pubints = pubkey.public_numbers()
