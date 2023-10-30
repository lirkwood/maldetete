# Maldetete
SSH server that stores incoming public keys and decrypts them on a quantum computer.

## Usage

`python server.py <port>`

By default it will serve on port 2222, as the ordinary port 22 is privileged on most Linux distros.

## Architecture
`server.py` contains a very basic SSH server implementation using [paramiko](https://docs.paramiko.org/en/latest/index.html).

`decrypt.py` has one entrypoint, the decrypt function, and it tries to derive the private key of an RSA key from the public key.

All modern SSH keys use >2048 bit keys, so breaking these keys is not viable. However, our server will accept any key, so if you send a key that is vulnerable (like the key created in `client.py`), it will decrypt it and print the private numbers.

The only purpose of `client.py` is to run a modified SSH client that is willing to use very small RSA keys. It generates the RSA key pair every time it runs, from specific numbers that can be read from the comments in the file.

Unfortunately, keys of a sufficiently small size to be breakable are *too* small to use with OpenSSL. Because of this limitation (security feature...) we simply forgo using the private key to sign any data. We do this by patching the python bindings to OpenSSL using `patch.py`. You should run `patch.py` before you attempt to connect using the client.

**NOTE** if you patch the environment you are running the server in, it will not work. The server will also not sign its outgoing data and the client will refuse to connect.

By not signing our outbound data, we can send the public key to the server in the correct format without having to write a new implementation of OpenSSL's RSA signature code. However, this means we cannot actually use the client to connect. This is not the end of the world - we can still use the normal OpenSSH client to connect to our server, so we know it works. In fact, when (if) quantum computers get good enough to actually run Shor's on reasonable key sizes, this exact server would work, and we could throw away the client in favour of any conformant SSH implementation.
