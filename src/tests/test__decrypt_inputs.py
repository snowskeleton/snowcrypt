import unittest

from ..snowcrypt.snowcrypt import decrypt_aaxc, decrypt_aax


class TestDecryptAaxcInputValidation(unittest.TestCase):
    def test_decrypt_aaxc_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            decrypt_aaxc(
                '/nonexistent/path/to/file.aaxc',
                '/tmp/out.m4a',
                'aa' * 16,
                'bb' * 16,
            )


class TestDecryptAaxInputValidation(unittest.TestCase):
    def test_decrypt_aax_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            decrypt_aax(
                '/nonexistent/path/to/file.aax',
                '/tmp/out.m4a',
                'abcdef01',
            )


if __name__ == '__main__':
    unittest.main()
