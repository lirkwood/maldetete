#!/usr/bin/env python3

from paramiko.pkey import PKey


def decrypt_pubkey(pubkey: PKey):
    if pubkey.algorithm_name == "RSA":
        print(pubkey.asbytes())
