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


class TruncatedFile(SnowcryptException):
    """The input ended mid-block: it was cut short, not mis-keyed."""
    pass
