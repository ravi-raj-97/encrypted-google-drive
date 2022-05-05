from enum import Enum


"""
Design definitions/aspects of the backend service.
"""


class RequestBodyField:
    Filename = "file_name"
    Password = "password"
    SharedSecrets = "shared_secrets"
    NewPassword = "new_password"
    Content = "content"


class Endpoint:
    # Create a brand new file
    Create = "create"
    # Read the contents of a file
    Read = "read"
    # Edit a file gaining access using shared secrets
    Update = "update"
    # delete a file
    Delete = "delete"

    # generate shared secrets for the currently open document
    SharedSecrets = "shared-secrets"
    # change the password for the currently open document
    ChangePassword = "change-password"
