import unittest
from Crypto.Cipher.AES import MODE_CBC, new as newAES
from hashlib import sha1
from ..snowcrypt.snowcrypt import deriveKeyIV, _sha
from ..snowcrypt.constants import *
from .constants import *


class MyTestCases(unittest.TestCase):
  def test__decrypt_local(self):
    create_test_file()
    with open(TEST_SAMPLE_FILE, 'rb') as file:
      deriveKeyIV(file, TEST_BYTES)


def create_test_file():
    checksum = bytes.fromhex('01' + 'f' * 20)
    adrmTag = bytes.fromhex('6164726d' + '00000038000000')
    adrmTagLeng = 12
    adrmRandomLeng = 48

    filename = TEST_SAMPLE_FILE
    effstring = 'f' * adrmRandomLeng
    adrm = bytes.fromhex(effstring + _swapEndian(TEST_BYTES))

    with open(filename, 'wb') as inStream:
      im_key = _sha(FIXEDKEY, bytes.fromhex(TEST_BYTES))
      iv = _sha(FIXEDKEY, im_key, bytes.fromhex(TEST_BYTES))
      key = im_key[:16]
      im_iv = iv[:16]

      # ADRM tag and length
      cipher = newAES(key, MODE_CBC, iv=im_iv)
      inStream.seek(ADRM_START - adrmTagLeng)
      inStream.write(adrmTag)
      inStream.write(bytes.fromhex('01'))
      cipher = newAES(key, MODE_CBC, iv=im_iv)
      writableAdrm = cipher.encrypt(_pad_16(adrm))
      inStream.write(writableAdrm)
      # inStream.write(
      #     cipher.encrypt(
      #         _pad_16(adrm + bytes.fromhex(TEST_BYTES))
      #     )
      # )

      cipher = newAES(key, MODE_CBC, iv=im_iv)
      checksum = _sha(key, iv)
      assert len(checksum) == 20
      inStream.write(bytes.fromhex('00000000' '00000001' '00000000'))
      inStream.write(checksum)


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
