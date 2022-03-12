
"""
Design definitions/aspects of the backend service.
"""


class RequestBodyFields:
    Filename = 'file_name'
    Password = 'password'


class Endpoints:
    """
    User does not have a file open
    """
    # Create a brand new file as the owner
    Create = 'create'
    # Edit a file gaining access using a password
    Edit = 'edit-owner'
    # Edit a file gaining access using shared secrets
    EditShared = 'edit-shared'
    """
    User has a file open
    """
    # generate shared secrets for the currently open document
    SharedSecrets = 'shared-secrets'
    # change the password for the currently open document
    ChangePassword = 'change-password'
