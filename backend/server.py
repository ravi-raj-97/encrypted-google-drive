from flask import Flask, request, render_template, redirect, url_for
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

drive.init()

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

    if not credential_bytes:
        # there were not authentication methods
        raise Exception("no authentication method given in request.")

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
    with open(filename, "rb") as f:
        # read the entire content of the file
        file_data = f.read()
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
    with open(filename, "w+b") as f:
        f.write(file_data)


def delete_file_bytes(filename: str):
    # TODO networking code

    # mock filesystem implementation
    os.remove(filename)


@app.errorhandler(ValueError)
def handle_verification_failure(e: ValueError):
    if "MAC" in str(e):
        return "password may be incorrect or the file is corrupt.", 401

    return "unknown error.", 400


@app.errorhandler(FileNotFoundError)
def handle_file_not_found(e):
    return "the file does not exist.", 404


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    return render_template("index.html")


@app.post("/" + Endpoint.Create)
def create_file():
    if request.headers.get("Content-Type") == "application/json":
        # read filename
        file_name = request.json[RequestBodyField.Filename]
        # prepare credential byte array
        credential_bytes = get_credential_bytes()

        if not drive.exists(file_name):
            file_bytes = crypto.encrypt_and_digest(credential_bytes, bytes())
            drive.write(file_name, file_bytes)
            return "", 201
        else:
            return f"the file `{file_name}` already exists.", 409

        # TODO: Clean-up old code after new func is verified to be working
        # # check if the file exists
        # try:
        #     download_file_as_bytes(file_name)
        # except Exception:
        #     # if file is valid, then encrypt a new version
            
        #     # upload the file with the new contents
        #     upload_file_bytes(file_name, file_bytes)

        #     return "", 201
        # else:
        #     return f"the file `{file_name}` already exists.", 409


@app.post("/" + Endpoint.Read)
def read_file():
    if request.headers.get("Content-Type") == "application/json":
        # read filename
        file_name = request.json[RequestBodyField.Filename]
        # prepare credential byte array
        credential_bytes = get_credential_bytes()
        
        # check if the file exists
        file_data = drive.read(file_name)

        # TODO: Clean-up old code after new func is verified to be working
        # file_data = download_file_as_bytes(file_name)

        # if file is valid, then encrypt a new version
        content = crypto.decrypt_and_verify(credential_bytes, file_data)
        # return the content of the file to the user
        return {"content": content}


@app.post("/" + Endpoint.Update)
def update_file():
    if request.headers.get("Content-Type") == "application/json":
        # read filename
        file_name = request.json[RequestBodyField.Filename]
        # read new file contents
        new_contents: str = request.json[RequestBodyField.Content]
        # prepare credential byte array
        credential_bytes = get_credential_bytes()
        
        # download file
        file_data = drive.read(file_name)

        # TODO: Clean-up old code after new func is verified to be working
        # file_data = download_file_as_bytes(file_name)

        # verify that the contents are correct
        crypto.decrypt_and_verify(credential_bytes, file_data)
        # if file is valid, then encrypt a new version
        updated_file_bytes = crypto.encrypt_and_digest(
            credential_bytes, new_contents.encode("UTF-8")
        )
        
        # upload the file with the new contents
        drive.write(file_name, updated_file_bytes)
        
        # TODO: Clean-up old code after new func is verified to be working
        # upload_file_bytes(file_name, updated_file_bytes)

        return "", 200


@app.post("/" + Endpoint.Delete)
def delete_file():
    if request.headers.get("Content-Type") == "application/json":
        # read filename
        file_name = request.json[RequestBodyField.Filename]
        # prepare credential byte array
        credential_bytes = get_credential_bytes()
        
        # download file
        file_data = drive.read(file_name)
        
        # TODO: Clean-up old code after new func is verified to be working
        # file_data = download_file_as_bytes(file_name)

        # verify that the contents are correct
        crypto.decrypt_and_verify(credential_bytes, file_data)
        # remove the file
        drive.delete(file_name)
        
        # TODO: Clean-up old code after new func is verified to be working
        # delete_file_bytes(file_name)

        return "", 204


@app.post("/" + Endpoint.ChangePassword)
def change_password():
    if request.headers.get("Content-Type") == "application/json":
        # prepare credential byte array
        credential_bytes = get_credential_bytes()
        # read file name
        file_name = request.json[RequestBodyField.Filename]
        # read the new password the user wants for the file
        new_password = request.json[RequestBodyField.NewPassword]
        # read file name
        file_data = drive.read(file_name)
        # decrypt the file
        file_contents = crypto.decrypt_and_verify(credential_bytes, file_data)
        # create new credential bytes
        credential_bytes = crypto.key_from_password(new_password)
        # encrypt the file with the new contents
        new_file_data = crypto.encrypt_and_digest(
            credential_bytes, file_contents.encode("UTF-8")
        )
        # upload this new file to the drive
        drive.write(file_name, new_file_data)

        # TODO: Clean-up old code after new func is verified to be working
        # # fetch the file
        # file_data = download_file_as_bytes(file_name)
        # # decrypt the file
        # file_contents = crypto.decrypt_and_verify(credential_bytes, file_data)

        # # create new credential bytes
        # credential_bytes = crypto.key_from_password(new_password)

        # # encrypt the file with the new contents
        # new_file_data = crypto.encrypt_and_digest(
        #     credential_bytes, file_contents.encode("UTF-8")
        # )

        # # upload this new file to the drive
        # upload_file_bytes(file_name, new_file_data)

        return "", 200


# TODO
@app.post("/" + Endpoint.SharedSecrets)
def get_shared_secrets():
    if request.headers.get("Content-Type") == "application/json":
        # read password field coming in from the user
        password = request.json[RequestBodyField.Password]
        # turn password into 32byte key
        credential_bytes = crypto.key_from_password(password)
        # return the list of shared shamir secrets
        shared_secrets = [
            f"{x[0]}-{x[1].hex()}"
            for x in crypto.create_shared_secrets(credential_bytes)
        ]

        return {"shared_secrets": shared_secrets}


if __name__ == "__main__":
    app.run(debug=True)
    drive.close()
