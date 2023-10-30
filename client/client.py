#!/usr/bin/env python3

from io import StringIO
from sys import argv
from socket import AF_INET, SOCK_STREAM, socket
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateNumbers,
    RSAPublicNumbers,
)
from cryptography.hazmat.primitives import serialization

from paramiko import RSAKey, Transport

## Key generation

# Starting nums:
# p = 7, q = 5
# n = p * q = 35
# (p-1)(q-1) = 6 * 4 = 24
# (1 < e < 24) & gcd(e, 24) = 1; e = 5
# ed ≡ 1 (mod 24); d = 5
#
# CRT params:
# dmp1 = d (mod p - 1) = 5 % 6 = 5
# dmq1 = d (mod q - 1) = 5 % 4 = 1
# iqmp * q = 1 (mod p); iqmp = 3

pubnums = RSAPublicNumbers(5, 35)
privnums = RSAPrivateNumbers(7, 5, 5, 5, 1, 3, pubnums)

pem_bytes = privnums.private_key().private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.TraditionalOpenSSL,
    encryption_algorithm=serialization.NoEncryption(),
)

string_reader = StringIO(pem_bytes.decode("utf-8"))
"""File like object containing our private key in PEM format."""

## Connecting

try:
    [user, dest] = argv[1].split("@", 1)

except IndexError:  # No arguments passed
    raise ValueError("Must provide a destination to connect to: user@server:port")

except ValueError:  # No @ in argument
    from os import getlogin

    user = getlogin()
    dest = argv[1]


try:
    [addr, port] = dest.split(":", 1)
    port = int(port)
except ValueError:  # No : in argument
    addr = dest
    port = 22

sock = socket(AF_INET, SOCK_STREAM)
sock.connect((addr, port))
with Transport(sock) as tsp:
    tsp.start_client()
    tsp.auth_publickey(user, RSAKey.from_private_key(string_reader))
