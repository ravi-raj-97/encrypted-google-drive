
from flask import Flask, request
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

# service = drive.init_drive_service()


@app.post('/' + Endpoints.Create)
def create_file():
    if request.headers.get('Content-Type') == 'application/json':
        file_name = request.json[RequestBodyFields.Filename]
        password = request.json[RequestBodyFields.Password]
        # make sure that no file already exists with this name.
        file_metadata = {'name': file_name}
        # upload = service.files().create(
        #     body=file_metadata,
        #     media_body="",
        #     fields='id',
        # ).execute()
        return "good!"


@app.post('/' + Endpoints.Edit)
def download_file():
    if request.headers.get('Content-Type') == 'application/json':
        file_name = request.json[RequestBodyFields.Filename]
        password = request.json[RequestBodyFields.Password]
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
        return "good!"


if __name__ == '__main__':
    app.run(debug=True)
