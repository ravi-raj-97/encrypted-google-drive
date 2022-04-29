from enum import Enum


"""
Design definitions/aspects of the backend service.
"""


class PasswordMode(Enum):
    Owner = "owner"
    Shared = "shared"


class RequestBodyField(Enum):
    Filename = "file_name"
    Password = "password"
    SharedSecrets = "shared_secrets"
    NewPassword = "new_password"
    Content = "content"


class Endpoint:
    # Create a brand new file as the owner
    Create = "create"
    # Edit a file gaining access using a password
    Edit = "edit-owner"
    # Edit a file gaining access using shared secrets
    EditShared = "edit-shared"

    # generate shared secrets for the currently open document
    SharedSecrets = "shared-secrets"
    # change the password for the currently open document
    ChangePassword = "change-password"
