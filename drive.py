from __future__ import print_function

import os.path
import datetime
import io

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/drive"]


def init(debug: bool = False):
    # Global copy of Google Drive API service and Debug flag
    global DEBUG, API
    DEBUG = debug

    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        if DEBUG:
            print("[DRIVE] Authorizing user...")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            if DEBUG:
                print("[DRIVE] Re-authorizing user...")
            creds.refresh(Request())
        else:
            if DEBUG:
                print("[DRIVE] Authorizing new user...")
            flow = InstalledAppFlow.from_client_secrets_file(
                "client_secret.json",
                SCOPES,
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # try to return the service
        API = build("drive", "v3", credentials=creds)
        if DEBUG:
            print("[DRIVE] Connected to Google Drive service successfully!")
        return API

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f"Unable to connect. Error occurred: {error}")
        exit(1)


def convert_to_RFC_datetime(year=1900, month=1, day=1, hour=0, minute=0):
    dt = datetime.datetime(year, month, day, hour, minute, 0).isoformat() + "Z"
    return dt


def exists(filename: str):
    try:
        response = (
            API.files()
            .list(
                q=f"name='{filename}' and trashed=false",
                spaces="drive",
                fields="nextPageToken, files(id)",
            )
            .execute()
        )
        if len(response["files"]) > 0:
            if DEBUG:
                print(f"[DRIVE] File <{filename}> already exists.")
            return True
        else:
            if DEBUG:
                print(f"[DRIVE] File <{filename}> doesn't exists.")
            return False
    except HttpError as err:
        print(
            "[DRIVE] <exists()> error. Status code: {0}, Reason: {1}".format(
                err.status_code, err.error_details
            )
        )


def get_id(filename: str):
    try:
        response = (
            API.files()
            .list(
                q=f"name='{filename}' and trashed=false",
                spaces="drive",
                fields="nextPageToken, files(id)",
            )
            .execute()
        )
        if DEBUG:
            print(f"[DRIVE] ID for <{filename}> retrieved.")
        return response["files"][0]["id"]
    except HttpError as err:
        print(
            "[DRIVE] <get_id()> error. Status code: {0}, Reason: {1}".format(
                err.status_code, err.error_details
            )
        )


def write(file_name: str, file_content: bytes):
    file_metadata = {"name": file_name}
    file_io_buffer = io.BytesIO(file_content)
    media = MediaIoBaseUpload(file_io_buffer, mimetype="text/plain")
    try:
        if not exists(file_name):
            # Create new file
            response = (
                API.files()
                .create(
                    body=file_metadata,
                    media_body=media,
                )
                .execute()
            )
            if DEBUG:
                print(f"[DRIVE] File <{file_name}> created.")
        else:
            # Update existing file
            response = (
                API.files()
                .update(
                    fileId=get_id(file_name),
                    body=file_metadata,
                    media_body=media,
                )
                .execute()
            )
            if DEBUG:
                print(f"[DRIVE] File <{file_name}> updated.")
        return response["id"]
    except HttpError as e:
        print(
            "[DRIVE] <write()> error. Status code: {0}, Reason: {1}".format(
                e.status_code, e.error_details
            )
        )


def read(filename: str):
    try:
        if exists(filename):
            response = (
                API.files()
                .get_media(
                    fileId=get_id(filename),
                )
                .execute()
            )
            if DEBUG:
                print(f"[DRIVE] CONTENT for <{filename}> retrieved.")
            return response
        else:
            raise FileNotFoundError
    except HttpError as err:
        print(
            "[DRIVE] <read()> error. Status code: {0}, Reason: {1}".format(
                err.status_code, err.error_details
            )
        )


def delete(filename: str):
    try:
        if exists(filename):
            response = (
                API.files()
                .delete(
                    fileId=get_id(filename),
                )
                .execute()
            )
            if DEBUG:
                print(f"[DRIVE] File <{filename}> deleted.")
            return response
        else:
            raise FileNotFoundError
    except HttpError as err:
        print(
            "[DRIVE] <delete()> error. Status code: {0}, Reason: {1}".format(
                err.status_code, err.error_details
            )
        )


def close():
    try:
        API.close()
    except HttpError as err:
        print(
            "[DRIVE] <close()> error. Status code: {0}, Reason: {1}".format(
                err.status_code, err.error_details
            )
        )
