import io
from random import randint
from typing import List
from hashlib import sha256

from Crypto.Protocol.SecretSharing import Shamir
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes

"""
Functions for performing crypographic operations.

in the end this may become a wrapper file for many of the functionalities
already provided in the pycryptodome package.
"""


SHARES: int = 5
SHARES_SUFFICIENT: int = 2


def create_shared_secrets(credential_bytes: bytes) -> list:
    return Shamir.split(SHARES_SUFFICIENT, SHARES, credential_bytes)


def key_from_shared(shared_secrets: list) -> bytes:
    # check whether the number of shared secerts in the input is enough to recreate the key
    if len(shared_secrets) >= SHARES_SUFFICIENT:
        raise Exception(
            f"required to have at least {SHARES_SUFFICIENT} shared secrets."
        )
    # return the assembled key, which is equivalent to the bytes of the password
    return Shamir.combine(shared_secrets)


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
