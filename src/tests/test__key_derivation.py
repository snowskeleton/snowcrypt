import unittest
from Crypto.Cipher.AES import MODE_CBC, new as newAES
from hashlib import sha1
from ..snowcrypt.snowcrypt import deriveKeyIV, _sha
from ..snowcrypt.constants import *
from .constants import *


class MyTestCases(unittest.TestCase):
  def test__decrypt_local(self):
    create_test_file(TEST_SAMPLE_FILE)
    with open(TEST_SAMPLE_FILE, 'rb') as file:
      deriveKeyIV(file, TEST_BYTES)


def create_test_file(filename):
    with open(filename, 'wb') as inStream:
      im_key = _sha(FIXEDKEY, bytes.fromhex(TEST_BYTES))
      iv = _sha(FIXEDKEY, im_key, bytes.fromhex(TEST_BYTES))[:16]
      key = im_key[:16]

      # ADRM tag and length
      tag = '6164726d' + '00000038000000'
      offset = ADRM_START - (int(len(tag) / 2) + 1)
      inStream.seek(offset)
      inStream.write(bytes.fromhex(tag))

      cipher = newAES(key, MODE_CBC, iv=iv)
      adrm = bytes.fromhex(_swapEndian('f' * ADRM_LENGTH + TEST_BYTES))
      inStream.write(bytes.fromhex('01') + cipher.encrypt(_pad_16(adrm)))

      # checksum
      inStream.write(bytes.fromhex('00000000' '00000001' '00000000'))
      inStream.write(_sha(key, iv))


def _pad_16(data: bytes, length: int = 16) -> bytes:
    length = length - (len(data) % length)
    return data + bytes([length])*length


if __name__ == '__main__':
    unittest.main()


def _sha(*bits: bytes, length: int = None):
    return sha1(b''.join(bits)).digest()[:length]


def _swapEndian(string: str):
    """turns 12345678 into 78563412
    """
    return "".join(string[i] + string[i + 1] for i in range(-2, -len(string) - 1, -2))
