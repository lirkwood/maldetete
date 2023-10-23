#!/usr/bin/env python3

from paramiko.pkey import PKey


def decrypt_pubkey(pubkey: PKey) -> bytes:
    if pubkey.algorithm_name == "RSA":
        print(pubkey.asbytes())
    return pubkey.get_fingerprint()
