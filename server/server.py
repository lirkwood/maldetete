#!/usr/bin/env python3

import socket
import threading
from paramiko import Channel, PKey, RSAKey, ServerInterface, Transport
from paramiko.common import AUTH_SUCCESSFUL, OPEN_SUCCEEDED
from pexpect import EOF, TIMEOUT, spawn
from threading import Thread
from argparse import ArgumentParser, Namespace

from decrypt import decrypt_pubkey

## SSH server


class Server(ServerInterface):
    def check_channel_request(self, _kind: str, _chanid: int) -> int:
        """Allow any client to open a communcations channel with the server."""
        return OPEN_SUCCEEDED

    def get_allowed_auths(self, _username: str) -> str:
        """Only allow public key authentication for any user
        to encourage sending pubkeys."""
        return "publickey"

    def check_auth_publickey(self, _username: str, key: PKey) -> int:
        """Always accept any pubkeys - and decrypt them."""
        if key.algorithm_name == "RSA":
            Thread(target=decrypt_pubkey, args=[key.key]).start()
        return AUTH_SUCCESSFUL

    def check_channel_pty_request(
        self,
        _channel: Channel,
        _term: bytes,
        _width: int,
        _height: int,
        _pixelwidth: int,
        _pixelheight: int,
        _modes: bytes,
    ) -> bool:
        """PTY request in SSH2 is almost exclusively used for opening a shell.
        We alert user request was approved but do no actual work."""
        return True

    def check_channel_shell_request(self, channel: Channel) -> bool:
        """Opens a shell for anyone who asks."""
        shell = spawn("/bin/bash")
        Shell(shell, channel).start()

        return True

    def get_banner(self) -> tuple[str, str]:
        return ("You are now using Team Cryptos very dodgy SSH server.", "en-US")


class Shell(threading.Thread):
    """This is a thread that runs a shell for a connected client.
    All logic is in the run method."""

    shell: spawn
    """pexpect process running a shell."""
    chan: Channel
    """A channel that is communicating with this shell."""

    def __init__(self, shell: spawn, chan: Channel) -> None:
        self.shell = shell
        self.chan = chan
        super().__init__()

    def run(self) -> None:
        """This method runs a shell for the connected user.
        All data sent down the channel is copied to the child shell.
        Output from the shell is sent back up the channel.
        Upon reading EOF from channel, we kill process and close channel."""

        while not self.chan.closed:
            if self.chan.recv_ready():
                self.shell.send(self.chan.recv(2048))
            else:
                try:
                    self.chan.send(self.shell.read_nonblocking(2048, 0))
                except TIMEOUT:
                    pass
                except EOF:
                    break

        if self.chan.active:
            self.chan.shutdown(2)
            self.chan.close()
        self.shell.kill(9)


## CLI


def parse_args() -> Namespace:
    parser = ArgumentParser(
        prog="maldetete",
        description="SSH server that breaks public keys using Shor's.",
    )

    parser.add_argument(
        "-p",
        "--port",
        required=False,
        help="The port to listen on for connections. Default is 2222.",
    )

    parser.add_argument(
        "-k",
        "--private-key",
        required=False,
        help="Path to a PEM encoded RSA private key to use as the identity of the server.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    port = int(args.port) if args.port is not None else 2222
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", port))

    if args.private_key is None:
        privkey = RSAKey.generate(2048)
        privkey_source = "that was newly generated."
    else:
        privkey = RSAKey.from_private_key_file(args.private_key)
        privkey_source = f"from the file path: {args.private_key}"

    print(f"Serving the server on port {port} using a private key {privkey_source}")

    while True:
        sock.listen(5)
        client, addr = sock.accept()
        print(f"Client connected from {addr}")

        server = Server()
        with Transport(sock=client) as tsp:
            event = threading.Event()

            tsp.add_server_key(privkey)
            tsp.start_server(server=server, event=event)

            channel = tsp.accept(20)
            if channel is None:
                continue

            while not channel.closed:
                ...
