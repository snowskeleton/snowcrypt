class SnowcryptException(Exception):
    pass


class CredentialMismatch(SnowcryptException):
    pass


class NotDecryptable(SnowcryptException):
    pass


class NotAnAudibleFile(SnowcryptException):
    pass


class DecryptionFailure(SnowcryptException):
    pass
