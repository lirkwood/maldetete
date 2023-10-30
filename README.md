# Maldetete
SSH server that stores incoming public keys and decrypts them on a quantum computer.

## Usage

`python server/server.py <port>`

By default it will serve on port 2222, as the ordinary port 22 is privileged on most Linux distros.

### Requirements

Just the python package `paramiko`.
Server also requires the package `pexpect` to serve the shell.

**CAVEAT** The `patch.py` modifies the Python environment it runs in. This breaks the OpenSSL RSA functionality (in a way that allows us to send a public key that is "too small").
This means that you will need separate Python environments for the server and the client.
This can be easily achieved with virtual environments e.g. [venv](https://docs.python.org/3/library/venv.html), [virtualenv](https://virtualenv.pypa.io/en/latest/), etc

## Architecture
`server/server.py` contains a very basic SSH server implementation using [paramiko](https://docs.paramiko.org/en/latest/index.html).

`server/decrypt.py` has one entrypoint, the decrypt function, and it tries to derive the private key of an RSA key from the public key.

`server/shors.py` is an implementation of Shor's algorithm by Todd Wildey that can be found [here](https://github.com/toddwildey/shors-python) under an MIT license. On my machine this took ~143 seconds to factor the integer 35, which is the component to be factorised of the default RSA public key generated in the client.

All modern SSH keys use >2048 bit keys, so breaking these keys is not viable. However, our server will accept any key, so if you send a key that is vulnerable (like the key created in `client/client.py`), it will decrypt it and print the private numbers.

`client/client.py` loads an RSA key from a file if provided one, otherwise it generates one from parameters documented in the file. It then runs an SSH client that is willing to use very small RSA keys.
The usage syntax is as follows: 
    `python client/client.py [-k <path to private key>] [<user>@]hostname[:<port>]`

`client/patch.py` is a script to patch the `cryptography` package depended on by paramiko. Unfortunately, keys of a sufficiently small size to be breakable are *too* small to use with OpenSSL. Because of this limitation (security feature...) we simply forgo using the private key to sign any data. We do this by patching the python bindings to OpenSSL using `client/patch.py`. You should run `client/patch.py` in the client Python environment before you attempt to connect using the client script.

By not signing our outbound data, we can send the public key to the server in the correct format without having to write a new implementation of OpenSSL's RSA signature code. However, this means we cannot actually use the client to connect. This is not the end of the world - we can still use the normal OpenSSH client to connect to our server, so we know it works. In fact, when (if) quantum computers get good enough to actually run Shor's on reasonable key sizes, this exact server would work (if provided with a quantum Shor's implementation), and we could throw away the client in favour of any conformant SSH implementation.
