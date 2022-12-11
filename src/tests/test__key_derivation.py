import unittest
from Crypto.Cipher.AES import MODE_CBC, new as newAES
from ..snowcrypt.snowcrypt import deriveKeyIV, _sha, _swapEndian, _pad_16
from ..snowcrypt.constants import FIXEDKEY, ADRM_START, ADRM_LENGTH
from .constants import TEST_BYTES
from io import BytesIO


class MyTestCases(unittest.TestCase):
    def test__key_derivation(self):
        file = BytesIO()
        create_test_adrm_file(file)
        deriveKeyIV(file, TEST_BYTES)
        file.close()


def create_test_adrm_file(file):
    im_key = _sha(FIXEDKEY, bytes.fromhex(TEST_BYTES))
    iv = _sha(FIXEDKEY, im_key, bytes.fromhex(TEST_BYTES))[:16]
    key = im_key[:16]

    # ADRM tag and length
    tag = '6164726d' + '00000038000000'
    offset = ADRM_START - (int(len(tag) / 2) + 1)
    file.seek(offset)
    file.write(bytes.fromhex(tag))

    cipher = newAES(key, MODE_CBC, iv=iv)
    adrm = 'f' * ADRM_LENGTH + TEST_BYTES
    adrm = bytes.fromhex(_swapEndian(adrm))
    file.write(bytes.fromhex('01') + cipher.encrypt(_pad_16(adrm)))

    # checksum
    file.write(bytes.fromhex('00000000' '00000001' '00000000'))
    file.write(_sha(key, iv))


if __name__ == '__main__':
    unittest.main()
