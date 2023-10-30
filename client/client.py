#!/usr/bin/env python3

from io import StringIO
from sys import argv
from socket import AF_INET, SOCK_STREAM, socket
from cryptography.hazmat.primitives.asymmetric.rsa import (
    RSAPrivateNumbers,
    RSAPublicNumbers,
)
from cryptography.hazmat.primitives import serialization
from argparse import ArgumentParser, Namespace

from paramiko import RSAKey, Transport


## Key generation


def gen_rsa() -> bytes:
    """
    Returns an RSA private key as bytes in PEM encoding.
    The parameters are shown below.

    Starting nums:
    p = 7, q = 5
    n = p * q = 35
    (p-1)(q-1) = 6 * 4 = 24
    (1 < e < 24) & gcd(e, 24) = 1; e = 5
    ed ≡ 1 (mod 24); d = 5

    Private nums:
    p = 7, q = 5, d = 5

    Public nums:
    n = 35, e = 5

    CRT params (optional optimisation):
    dmp1 = d (mod p - 1) = 5 % 6 = 5
    dmq1 = d (mod q - 1) = 5 % 4 = 1
    iqmp * q = 1 (mod p); iqmp = 3
    """

    pubnums = RSAPublicNumbers(5, 35)
    privnums = RSAPrivateNumbers(7, 5, 5, 5, 1, 3, pubnums)

    return privnums.private_key().private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )


## Connecting


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog="maldetete-client",
        description="SSH client that can use very small RSA keys (almost).",
    )

    parser.add_argument(
        "server",
        help="Server to connect to. "
        + "Of the form: [<username>@]<server address>[:<server port>]",
    )

    parser.add_argument(
        "-k",
        "--private-key",
        required=False,
        help="Path to a PEM encoded RSA private key to use as the identity of the client.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    try:
        [user, dest] = args.server.split("@", 1)

    except IndexError:  # No arguments passed
        raise ValueError("Must provide a destination to connect to: user@server:port")

    except ValueError:  # No @ in argument
        from os import getlogin

        user = getlogin()
        dest = args.server

    try:
        [addr, port] = dest.split(":", 1)
        port = int(port)
    except ValueError:  # No : in argument
        addr = dest
        port = 22

    if args.private_key is not None:
        privkey = RSAKey.from_private_key_file(args.private_key)
    else:
        privkey = RSAKey.from_private_key(StringIO(gen_rsa().decode("utf-8")))

    sock = socket(AF_INET, SOCK_STREAM)
    sock.connect((addr, port))
    with Transport(sock) as tsp:
        tsp.start_client()
        tsp.auth_publickey(user, privkey)
