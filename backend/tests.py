import requests
from definitions import *

"""
Test File to make sure that the endpoints work correctly before use with the frontend.
"""

SERVER_URL = 'http://127.0.0.1:5000/'

HEADERS = {'Content-Type': 'application/json'}

"""
Create Tests
"""


def create_tests(server_url: str):
    body = {
        RequestBodyFields.Filename: 'test_file_name',
        RequestBodyFields.Password: 'example_password',
    }
    response = requests.post(server_url, headers=HEADERS, json=body)
    assert response.text == "good!"
    print()


create_tests(SERVER_URL + Endpoints.Create)

"""
Edit Tests
...
"""
