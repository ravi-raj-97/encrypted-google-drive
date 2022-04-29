from flask import Flask, request
from flask_cors import CORS
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

import os
import crypto
import drive
from definitions import *


app = Flask(__name__)
CORS(app)

# service = drive.init_drive_service()


def get_credential_bytes():
    # prepare credential byte array
    credential_bytes: bytes

    if RequestBodyField.Password in request.json:
        # read the password json field
        password = request.json[RequestBodyField.Password]
        # turn the password into valid credential bytes
        credential_bytes = crypto.key_from_password(password)

    elif RequestBodyField.SharedSecrets in request.json:
        # read shared secret list
        # TODO decide what to parse this as
        shared_secrets: List[str] = request.json[RequestBodyField.SharedSecrets]
        # create credentials key from shared secrets
        credential_bytes = crypto.key_from_shared(shared_secrets)

    return credential_bytes


def download_file_as_bytes(filename: str) -> bytes:
    # network calls to get the file

    # response = service.files().list(
    #     q=f"name='{file_name}'",
    #     spaces='drive',
    #     fields='nextPageToken, files(id, name)',
    # ).execute()
    # files = response.get('files', [])
    # # test for the existence of the file
    # if not files:
    #     return {"error": f"no files exists with the name {file_name}"}

    # requested_file = files[0]

    # mock filesystem implementation
    if not os.path.exists(filename):
        raise Exception("file doesnt exist")

    with open(filename) as f:
        # read the entire content of the file
        file_data = filef.read()
        # returns the file as an array of bytes
        return file_data


def upload_file_bytes(filename: str, file_data: bytes):
    # TODO networking code
    # # make sure that no file already exists with this name.
    # file_metadata = {"name": file_name}
    # # upload = service.files().create(
    # #     body=file_metadata,
    # #     media_body="",
    # #     fields='id',
    # # ).execute()

    # mock filesystem implementation
    with open(filename, "w") as f:
        f.write(file_data)


@app.post("/" + Endpoint.Create)
def create_file():
    if request.headers.get("Content-Type") == "application/json":
        # read filename
        file_name = request.json[RequestBodyField.Filename]
        # read file contents
        contents = request.json[RequestBodyField.Content]
        # prepare credential byte array
        credential_bytes = get_credential_bytes()

        # check if the file exists
        if download_file_as_bytes(file_name):
            return "file already exists"

        # if file is valid, then encrypt a new version
        file_bytes = crypto.encrypt_and_digest(credential_bytes, contents)
        # upload the file with the new contents
        upload_file_bytes(file_name, file_bytes)


@app.post("/" + Endpoint.Edit)
def update_file():
    if request.headers.get("Content-Type") == "application/json":
        # read filename
        file_name = request.json[RequestBodyField.Filename]
        # read new file contents
        new_contents = request.json[RequestBodyField.Content]
        # prepare credential byte array
        credential_bytes = get_credential_bytes()
        # download file
        file_data = download_file_as_bytes(file_name)
        # verify that the contents are correct
        crypto.decrypt_and_verify(credential_bytes, file_data)
        # if file is valid, then encrypt a new version
        updated_file_bytes = crypto.encrypt_and_digest(credential_bytes, new_contents)
        # upload the file with the new contents
        upload_file_bytes(file_name, updated_file_bytes)


@app.post("/" + Endpoint.SharedSecrets)
def get_shared_secrets():
    if request.headers.get("Content-Type") == "application/json":
        # read password field coming in from the user
        password = request.json[RequestBodyField.Password]
        # return the list of shared shamir secrets
        return {
            "keys": [
                (x[0], x[1].hex()) for x in crypto.create_shared_secrets(bytearray(16))
            ]
        }
        # crypto.key_from_password(password))


@app.post("/" + Endpoint.ChangePassword)
def change_password():
    if request.headers.get("Content-Type") == "application/json":
        # prepare credential byte array
        credential_bytes = get_credential_bytes()

        if not credential_bytes:
            # there were not authentication methods
            raise Exception("no authentication method given in request.")

        # read file name
        file_name = request.json[RequestBodyField.Filename]
        # fetch the file
        file_data = download_file_as_bytes(file_name)
        # decrypt the file
        file_contents = crypto.decrypt_and_verify(credential_bytes, file_data)

        # read the new password the user wants for the file
        new_password = request.json[RequestBodyField.NewPassword]
        # create new credential bytes
        credential_bytes = crypto.key_from_password(new_password)

        # encrypt the file with the new contents
        new_file_data = crypto.encrypt_and_digest(credential_bytes, file_contents)

        # upload this new file to the drive
        upload_file_bytes(file_name, file_data)


if __name__ == "__main__":
    app.run(debug=True)
