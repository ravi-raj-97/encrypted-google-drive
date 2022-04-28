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


def create_shared_secrets(key: bytes) -> List[(int, str)]:
    return Shamir.split(SHARES_SUFFICIENT, SHARES, key)


def compute_salted_hash(credenial_bytes: bytes, r: int, salt: bytes) -> bytes:
    key = bytes()
    for i in range(1, r):
        key = sha256(key + credenial_bytes + salt).digest()
    return key


def key_from_password(password: str):
    key_bytes = password.encode("UTF-8")
    return compute_salted_hash(key_bytes, r, salt)


def key_from_shared(shared_secrets: List[(int, str)]):
    # check whether the number of shared secerts in the input is enough to recreate the key
    if len(shared_secrets) >= SHARES_SUFFICIENT:
        raise Exception(
            f"required to have at least {SHARES_SUFFICIENT} shared secrets."
        )

    key_bytes = Shamir.combine(shared_secrets)
    return compute_salted_hash(key_bytes, r, salt)


def encrypt_and_digest(credential_bytes: bytes, plaintext: bytes):
    # generate random nonce value
    nonce = get_random_bytes(16)
    # generate random salt and r values for hashing
    salt = get_random_bytes(8)
    r = randint(1, 128).to_bytes(8, "big")

    # generate key from credentials
    key = compute_salted_hash(credenial_bytes, r, salt)
    # create the AES-GCM cipher
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    # encrypt the data
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)

    # IO buffer to hold the encrypted file data
    file_data = io.BytesIO()
    # write metadata and content to file buffer (salt | r | nonce | tag | ciphertext)
    file_data.write(salt + r + nonce + tag + ciphertext)

    # save data to the cloud
    # ...


def decrypt_and_verify(credential_bytes: bytes, file_data: bytes) -> str:
    # read the data through a byte buffer
    file_bytes = io.BytesIO(file_data)
    # read all of the components from the file data
    salt, r, nonce, tag, ciphertext = (
        file_bytes.read(16),
        int.from_bytes(file_bytes.read(8), "big"),
        file_bytes.read(8),
        file_bytes.read(32),
        file_bytes.read(),
    )
    # compute hashed key
    key = compute_salted_hash(credenial_bytes, r, salt)
    # create cipher using stored nonce
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    # decrypt and verify
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    # return the contents of the file
    return plaintext


def download_file_as_bytes(filename: str) -> bytes:
    # network calls to get the file
    file_data = bytes()
    # returns the file as an array of bytes
    return file_data
