#!/usr/bin/env python3

from math import log2
from re import VERBOSE
from typing import Optional
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from shors import shors


def decrypt_pubkey(pubkey: RSAPublicKey):
    """
    Derives a private RSA key from the public key and prints its parameters.

    RSA keys have the satisfy the following equation:
    m^(e*d) ≡ m (mod n)
    Here m is the message, e and n are known are d is to be found.
    """
    pubints = pubkey.public_numbers()
    if log2(pubints.n) > 8:
        print(
            "Factoring an integer larger than 8 bits is likely going to take a long time."
            + " Try with something smaller."
        )
        return

    print(f"Decrypting public key with numbers {pubints}")
    factors = shors(pubints.n, attempts=20, neighborhood=0.01, numPeriods=2)
    if factors is None or factors is False:
        print(f"Failed to factors integer {pubints.n}")
        return

    [p, q] = factors
    totient = (p - 1) * (q - 1)
    d = pow(pubints.e, -1, totient)
    print(f"Found private numbers: p = {p}, q = {q}, d = {d}")
