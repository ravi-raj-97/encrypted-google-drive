import os
import requests
from definitions import *

"""
Test File to make sure that the endpoints work correctly before use with the frontend.
"""

SERVER_URL = "http://127.0.0.1:5000/"

HEADERS = {"Content-Type": "application/json"}


def main():
    def post(endpoint: str, data: dict):
        return requests.post(
            url=SERVER_URL + endpoint,
            headers=HEADERS,
            json=data,
        )

    def get(endpoint: str, query: str):
        return requests.get(
            url=SERVER_URL + endpoint + "?" + query,
            headers=HEADERS,
        )

    """ SETUP TESTBED """

    test_filename = "example_filename"

    test_password = "quite secret isnt it"
    test_updated_password = "hey its a new password"

    test_content1 = "a long string with a good amount of words"
    test_content2 = "content was changed"

    # cleanup test bed
    delete_response = post(
        Endpoint.Delete,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
        },
    )

    delete_response = post(
        Endpoint.Delete,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_updated_password,
        },
    )

    """ RUN TESTS """

    # Create a new file

    create_response = post(
        Endpoint.Create,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
        },
    )

    assert create_response.status_code == 201

    # Try to create the same file twice and get an error

    create_duplicate_response = post(
        Endpoint.Create,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: "empty",
        },
    )

    assert create_duplicate_response.status_code == 409
    assert "already exists" in create_duplicate_response.text

    # Try to read the created file using a bad password

    bad_password_read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: "wrong password",
        },
    )

    assert bad_password_read_response.status_code == 401
    assert "incorrect" in bad_password_read_response.text

    # Read the file using the correct password

    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
        },
    )

    assert read_response.status_code == 200

    # Change the content in the file

    update_request = post(
        Endpoint.Update,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
            RequestBodyField.Content: test_content1,
        },
    )

    assert update_request.status_code == 200

    # Check that the content has been changed to the new value

    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
        },
    )

    assert read_response.status_code == 200
    assert test_content1 in read_response.text

    # Change the content in the file

    update_request = post(
        Endpoint.Update,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
            RequestBodyField.Content: test_content2,
        },
    )

    assert update_request.status_code == 200

    # Check that the content has been changed to the new value

    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
        },
    )

    assert read_response.status_code == 200
    assert test_content2 in read_response.text

    # change password

    change_password_response = post(
        Endpoint.ChangePassword,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
            RequestBodyField.NewPassword: test_updated_password,
        },
    )

    assert change_password_response.status_code == 200

    # Try to access the file using the old password

    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_password,
        },
    )

    assert read_response.status_code == 401
    assert "incorrect" in read_response.text

    # Then try it with the new password

    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_updated_password,
        },
    )

    assert read_response.status_code == 200
    assert test_content2 in read_response.text

    # try to read a file that doesnt exist
    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: "not real",
            RequestBodyField.Password: "doesnt matter",
        },
    )

    assert read_response.status_code == 404

    # generate the shared secrets for a given password

    share_count = 4
    threshold = 2

    generate_shared_secrets_response = post(
        Endpoint.SharedSecrets,
        {
            RequestBodyField.Password: test_updated_password,
            RequestBodyField.Shares: share_count,
            RequestBodyField.Threshold: threshold,
        },
    )

    generated_secrets: list = generate_shared_secrets_response.json()[
        RequestBodyField.SharedSecrets
    ]

    assert len(generated_secrets) == share_count

    # try to access the file with the correct amount of shared secrets

    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.SharedSecrets: ",".join(
                (generated_secrets[0], generated_secrets[-1])
            ),
        },
    )

    assert read_response.status_code == 200
    assert test_content2 in read_response.text

    # try to access the file while missing secrets or using incorrect secrets

    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.SharedSecrets: generated_secrets[0],
        },
    )

    assert read_response.status_code == 401

    # try to read a file that doesnt exist
    read_response = post(
        Endpoint.Read,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.SharedSecrets: ",".join(
                (
                    generated_secrets[0],
                    "3-df6649b96881ff3da76282dfe7501d59a4824e7e3db9862d7b45840b5b16b959",
                )
            ),
        },
    )

    assert read_response.status_code == 401

    # delete the file

    delete_response = post(
        Endpoint.Delete,
        {
            RequestBodyField.Filename: test_filename,
            RequestBodyField.Password: test_updated_password,
        },
    )

    assert delete_response.status_code == 204


if __name__ == "__main__":
    main()
