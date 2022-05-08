import io
from random import randint
from typing import List
from hashlib import sha256

import shamirs
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

"""
Functions for performing crypographic operations.

in the end this may become a wrapper file for many of the functionalities
already provided in the pycryptodome package.
"""

# credit to https://github.com/lapets for the intuition on computing shamir secrets in the interger domain with python modulo inverse

# prime modulo close to the 256 bit limit of AES-256
_PRIME: int = 2**256 - 189


def create_shared_secrets(
    credential_bytes: bytes, share_count: int = 5, shares_sufficient: int = 3
) -> list:
    if shares_sufficient > 3:
        raise Exception("cannot set threshold to a value greater than 3")

    if share_count > 5:
        raise Exception("share count cannot be greater than 5")

    if shares_sufficient > share_count:
        raise Exception("share count should not be less than the sufficient threshold.")

    int_secret = int.from_bytes(credential_bytes, "big")

    shares = dict()
    # Random polynomial coefficients.
    coefficients: List[int] = [int_secret] + [
        randint(0, _PRIME - 1) for _ in range(1, shares_sufficient)
    ]

    # Compute each share such that shares[i] = f(i).
    for i in range(1, share_count + 1):
        shares[i] = coefficients[0]
        for j in range(1, len(coefficients)):
            shares[i] = (shares[i] + coefficients[j] * pow(i, j)) % _PRIME

    return [f'{i}-{format(s, "x")}' for i, s in shares.items()]


def key_from_shared(shared_secrets: List[str]) -> bytes:
    def inv(a: int, prime: int):
        return pow(a, prime - 2, prime)

    points = dict()
    for indexed_secret in shared_secrets:
        index, secret_hex = indexed_secret.split("-")
        points[int(index)] = int(secret_hex, 16)

    # Compute the Lagrange coefficients at ``0``.
    coefficients = dict()
    for i, y_i in enumerate(points.keys(), start=1):
        coefficients[i] = 1
        for j, y_j in enumerate(points.keys(), start=1):
            if y_i != y_j:
                coefficients[i] = (
                    coefficients[i] * (-y_j) * inv(y_i - y_j, _PRIME)
                ) % _PRIME

    key = 0
    # compute using horners theorem for computing polynomials
    for i, g in enumerate(points.values(), start=1):
        key = (key + g * coefficients[i]) % _PRIME

    # return the assembled key, which is equivalent to the bytes of the password
    return key.to_bytes(32, "big")


def key_from_password(password: str) -> bytes:
    return sha256(password.encode("UTF-8")).digest()


def compute_salted_hash(credenial_bytes: bytes, salt: bytes) -> bytes:
    key = bytes()
    r = 10
    for i in range(1, r):
        key = sha256(key + credenial_bytes + salt).digest()
    return key


def encrypt_and_digest(credential_bytes: bytes, plaintext: bytes) -> bytes:
    # generate random nonce value
    nonce = get_random_bytes(16)
    # generate random salt for hashing
    salt = get_random_bytes(16)
    # generate key from credentials
    key = compute_salted_hash(credential_bytes, salt)
    # create the AES-GCM cipher
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    # encrypt the data
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # IO buffer to hold the encrypted file data
    file_data = io.BytesIO()
    # write metadata and content to file buffer (salt | nonce | tag | ciphertext)
    file_data.write(salt + nonce + tag + ciphertext)

    # reset the reading pointer
    file_data.seek(0)
    # return all of the bytes of this file
    return file_data.read()


def decrypt_and_verify(credential_bytes: bytes, file_data: bytes) -> str:
    # read the data through a byte buffer
    file_bytes = io.BytesIO(file_data)
    # read all of the components from the file data
    salt, nonce, tag, ciphertext = (
        file_bytes.read(16),
        file_bytes.read(16),
        file_bytes.read(16),
        file_bytes.read(),
    )
    # compute hashed key
    key = compute_salted_hash(credential_bytes, salt)
    # create cipher using stored nonce
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    # decrypt and verify
    plaintext: bytes = cipher.decrypt_and_verify(ciphertext, tag)
    # return the contents of the file
    return plaintext.decode("UTF-8")


if __name__ == "__main__":
    password = "test string to verify that the shared secrets is working"
    pass_bytes = key_from_password(password)
    print("hashed pass:\n\t", pass_bytes)
    shared_secrets = create_shared_secrets(pass_bytes)
    print("created secrets:")
    for x in shared_secrets:
        print("\t", x)
    shared_bytes = key_from_shared(shared_secrets)
    print("assembled secret:\n\t", shared_bytes)
