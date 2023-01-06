import unittest
from io import BytesIO
from Crypto.Cipher.AES import MODE_CBC, new as newAES
from ..snowcrypt.constants import FIXEDKEY, ADRM_START, ADRM_LENGTH
from ..snowcrypt.localExceptions import CredentialMismatch
from ..snowcrypt.adrm_key_derivation import deriveKeyIV, _sha, _swapEndian, _pad_16
from .constants import TEST_BYTES


class MyTestCases(unittest.TestCase):
    def test__key_derivation_with_good_key(self):
        file = create_test_file(TEST_BYTES)
        deriveKeyIV(file, TEST_BYTES)
        file.close()

    def test__key_derivation_with_bad_key(self):
        garbage = 'abc123ff'  # random hex string, different than TEST_BYTES
        file = create_test_file(garbage)
        self.assertRaises(CredentialMismatch, deriveKeyIV, file, TEST_BYTES)
        file.close()


def create_test_file(activation_bytes: str) -> BytesIO:
    """creates BytesIO() object and returns it.
    Be sure to call obj.close() when you're done!

    Args:
        activation_bytes (str): seed

    Returns:
        BytesIO: adrm example
    """
    file = BytesIO()
    bytebytes = bytes.fromhex(activation_bytes)
    im_key = _sha(FIXEDKEY, bytebytes)
    true_iv = _sha(FIXEDKEY, im_key, bytebytes)[:16]
    true_key = im_key[:16]

    # ADRM tag and length
    tag = '6164726d' + '00000038000000'
    offset = ADRM_START - (int(len(tag) / 2) + 1)
    file.seek(offset)
    file.write(bytes.fromhex(tag))

    cipher = newAES(true_key, MODE_CBC, iv=true_iv)
    adrm = 'f' * ADRM_LENGTH + activation_bytes
    adrm = bytes.fromhex(_swapEndian(adrm))
    file.write(bytes.fromhex('01') + cipher.encrypt(_pad_16(adrm)))

    # checksum
    file.write(bytes.fromhex('00000000' '00000001' '00000000'))
    file.write(_sha(true_key, true_iv))
    return file

if __name__ == '__main__':
    unittest.main()
