# Maldetete
SSH server that stores incoming public keys and decrypts them on a simulated quantum Shor's algoritm, plus a client that can send RSA public keys small enough to break.

## Things that don't work

### Client

+ RSA keys less than 512 bits, unless you patch your environment
+ Any actual SSH functionality other than sending a public key over SSH, in the patched environment
+ Interactive commands during an SSH session (vi etc.)

### Server

+ Breaking RSA keys > 8 bits in size.

## Requirements

### Both
+ `paramiko`

### Just Server
+ `pexpect`

## Usage

### Environment

The client cannot send RSA keys smaller than 512 bits with running `client/patch.py` first. The script modifies a dependency in the environment it runs in, replacing the binding to an OpenSSL function with a no-op. This lets us send public keys that are smaller than normal. It also means we can't actually carry out a full SSH session — just send the key.

`client/unpatch.py` undoes the patch and restores the original version of the package.

This means that you will need separate Python environments for the server and the client.
This can be easily achieved with virtual environments e.g. [venv](https://docs.python.org/3/library/venv.html), [virtualenv](https://virtualenv.pypa.io/en/latest/), etc

If you don't want to bother, you can simply start the server before patching.

### CLI

When in doubt, try `python <server/server.py or client/client.py> -h` for a help.

**NOTE** When using the provided client in the patched environment (more about this below), it will fail with a message "Authentication Failed".

### Server

`python server/server.py [-h, --help] [-p <port>] [-k <path to private key>]`

By default it will serve on port 2222, 22 is usually a privileged port.
If provided with a private key it will use this as an identity. Otherwise it will generate its own.
There is a key provided in the root of the repo called `hostkey`. This is useful because by default OpenSSH aborts the connection if the host key of a server changes after you have connected to it once.

### Client

`python client/client.py [-h, --help] [-k <path to private key>] [<user>@]hostname[:<port>]`

**NOTE** Run `client/patch.py` first.

If not provided with a private key it will generate its own from parameters documented in the file. This will be the same key every time, and the number to factor with Shor's is 35 in this case.


## Architecture

### Server
`server/server.py` contains a very basic SSH server implementation using [paramiko](https://docs.paramiko.org/en/latest/index.html).

`server/decrypt.py` has one entrypoint, the decrypt function, and it tries to derive the private key of an RSA key from the public key.

Currently , so breaking these keys is not viable. However, our server will accept any key, so if you send a key that is vulnerable (like the key created in `client/client.py`), it will decrypt it and print the private numbers.

`server/shors.py` is an implementation of Shor's algorithm by Todd Wildey that can be found [here](https://github.com/toddwildey/shors-python). On my machine this took ~143 seconds to factor the integer 35, which is the component to be factorised of the default RSA public key generated in the client.

### Client

`client/client.py` loads an RSA key from a file if provided one, otherwise it generates one from parameters documented in the file. It then runs an SSH client that is willing to use very small RSA keys.

`client/patch.py` should be run before running the client. This is covered in the environment section above.

## Notes on this implementation

By having our client not sign our outbound data (via the patch), we can send the public key to the server in the correct format without having to write a new implementation of OpenSSL's RSA signature code. However, this means we cannot actually use the client to connect. This is not the end of the world - we can still use the normal OpenSSH client to connect to our server, so we know it works. 
