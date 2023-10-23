# Maldetete
SSH server that stores incoming public keys and decrypts them on a quantum computer.

## Usage

`python server.py <port>`

By default it will serve on port 2222, as the ordinary port 22 is privileged on most Linux distros.

## Architecture
`server.py` contains a very basic SSH server implementation using [paramiko](https://docs.paramiko.org/en/latest/index.html).
Eventually we would like to create a temporary user, home directory, permissions etc for any user that logs in, to make the experience more convincing. As it is you can only run commands as the user hosting the SSH server.

This is also an issue if you run server as root - you have just let anyone log into your machine as root! So don't do that :)

`decrypt.py` has one entrypoint, the decrypt function, and it tries to derive the private key of an RSA key from the public key.

All modern SSH keys use >2048 bit keys, and they hash them aswell, so breaking these keys is not viable. However, our server will accept any key, so if you send a key that is vulnerable... 
