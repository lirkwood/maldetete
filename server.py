#!/usr/bin/env python3

from os import read, write
import socket
import threading
from paramiko import Channel, PKey, RSAKey, ServerInterface, Transport
from paramiko.common import AUTH_SUCCESSFUL, OPEN_SUCCEEDED
from pty import openpty
from subprocess import PIPE, Popen
from pexpect import EOF, TIMEOUT, spawn
import select

from decrypt import decrypt_pubkey


class Server(ServerInterface):
    def __init__(self) -> None:
        super().__init__()

    def get_allowed_auths(self, username: str) -> str:
        return "publickey"

    def check_auth_publickey(self, username: str, key: PKey) -> int:
        decrypt_pubkey(key)
        return AUTH_SUCCESSFUL

    def check_channel_request(self, kind: str, chanid: int) -> int:
        return OPEN_SUCCEEDED

    def check_channel_pty_request(
        self,
        channel: Channel,
        term: bytes,
        width: int,
        height: int,
        pixelwidth: int,
        pixelheight: int,
        modes: bytes,
    ) -> bool:
        return True

    def check_channel_shell_request(self, channel: Channel) -> bool:
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
        Output from the shell is sent back up the channel."""
        while not self.chan.closed:
            if self.chan.recv_ready():
                self.shell.send(self.chan.recv(2048))
            else:
                try:
                    self.chan.send(bytes(self.shell.read_nonblocking(2048, 0)))
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
