#!/usr/bin/env python3

import socket
from sys import argv
import threading
from paramiko import Channel, PKey, RSAKey, ServerInterface, Transport
from paramiko.common import AUTH_SUCCESSFUL, OPEN_SUCCEEDED
from pexpect import EOF, TIMEOUT, spawn

from decrypt import decrypt_pubkey


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
        decrypt_pubkey(key)
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


sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

try:
    sock.bind(("0.0.0.0", int(argv[1])))
except (ValueError, IndexError) as exc:
    sock.bind(("0.0.0.0", 2222))

while True:
    sock.listen(5)
    client, addr = sock.accept()
    print(f"Client connected from {addr}")

    server = Server()
    with Transport(sock=client) as tsp:
        event = threading.Event()
        tsp.add_server_key(RSAKey.from_private_key_file("hostkey"))
        tsp.start_server(server=server, event=event)

        channel = tsp.accept(20)
        if channel is None:
            continue

        while not channel.closed:
            ...
