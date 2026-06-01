import unittest

from ..snowcrypt.localExceptions import (
    SnowcryptException,
    CredentialMismatch,
    NotDecryptable,
    NotAnAudibleFile,
    DecryptionFailure,
)


class TestExceptionHierarchy(unittest.TestCase):
    def test_all_inherit_from_snowcrypt_exception(self):
        for exc_class in [CredentialMismatch, NotDecryptable,
                          NotAnAudibleFile, DecryptionFailure]:
            self.assertTrue(
                issubclass(exc_class, SnowcryptException),
                f"{exc_class.__name__} should inherit from SnowcryptException"
            )

    def test_snowcrypt_exception_inherits_from_exception(self):
        self.assertTrue(issubclass(SnowcryptException, Exception))

    def test_credential_mismatch_can_be_raised_and_caught(self):
        with self.assertRaises(SnowcryptException):
            raise CredentialMismatch("bad creds")

    def test_not_decryptable_can_be_raised_and_caught(self):
        with self.assertRaises(SnowcryptException):
            raise NotDecryptable("missing key")

    def test_not_an_audible_file_can_be_raised_and_caught(self):
        with self.assertRaises(SnowcryptException):
            raise NotAnAudibleFile("wrong extension")

    def test_decryption_failure_can_be_raised_and_caught(self):
        with self.assertRaises(SnowcryptException):
            raise DecryptionFailure("size mismatch")

    def test_exception_message_preserved(self):
        msg = "test error message"
        for exc_class in [SnowcryptException, CredentialMismatch,
                          NotDecryptable, NotAnAudibleFile, DecryptionFailure]:
            exc = exc_class(msg)
            self.assertEqual(str(exc), msg)


if __name__ == '__main__':
    unittest.main()
