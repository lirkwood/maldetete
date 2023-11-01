#!/usr/bin/env python3

if __name__ == "__main__":
    from cryptography.hazmat.backends.openssl import rsa

    try:
        with open(rsa.__file__ + ".bkp", "r") as bkp:
            with open(rsa.__file__, "w") as mod:
                mod.write(bkp.read())
        print("Successfully unpatched.")
    except FileNotFoundError:
        raise FileNotFoundError(
            "Unable to locate backup of module."
            + " Run 'pip -U --force-reinstall cryptography' to restore the package manually."
        )
