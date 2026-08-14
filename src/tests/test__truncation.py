import io
import unittest
from struct import pack_into

from ..snowcrypt.localExceptions import TruncatedFile
from ..snowcrypt.snowcrypt import Translator, _decrypt_aavd, fuint

KEY = bytes.fromhex('f1c443f8db16304d24edc1245e278eaf')
IV = bytes.fromhex('9024b63436da4986ec5ac1f56729c0e4')


def _translator_for(block_length):
    """A Translator primed so next(fuint) yields block_length."""
    t = Translator()
    pack_into(fuint[0], t.buf, 0, block_length)
    return t


class TestTruncatedInput(unittest.TestCase):
    """
    A block's encrypted length is masked to a 16-byte boundary, so AES can
    only ever be handed a misaligned buffer when the file ended early. Saying
    'truncated' points at the real problem; the raw AES error talks about
    padding and reads like a bad key.
    """

    def test_short_read_raises_truncated_file(self):
        # Claims 256 encrypted bytes, supplies 100.
        stream = io.BytesIO(b'\x00' * 100)
        with self.assertRaises(TruncatedFile):
            _decrypt_aavd(stream, KEY, IV, _translator_for(256))

    def test_empty_stream_raises_truncated_file(self):
        stream = io.BytesIO(b'')
        with self.assertRaises(TruncatedFile):
            _decrypt_aavd(stream, KEY, IV, _translator_for(64))

    def test_error_names_the_byte_counts(self):
        stream = io.BytesIO(b'\x00' * 32)
        with self.assertRaises(TruncatedFile) as ctx:
            _decrypt_aavd(stream, KEY, IV, _translator_for(256))
        message = str(ctx.exception)
        self.assertIn('256', message)
        self.assertIn('32', message)
        self.assertIn('incomplete', message)

    def test_complete_block_decrypts(self):
        """The guard must not fire on a whole block."""
        # 48 encrypted bytes (a multiple of 16) plus 5 trailing plain bytes.
        length = 48 | 5
        stream = io.BytesIO(b'\x00' * 48 + b'abcde')
        data = _decrypt_aavd(stream, KEY, IV, _translator_for(length))
        self.assertEqual(len(data), 53)
        self.assertTrue(data.endswith(b'abcde'))

    def test_block_with_no_trailing_bytes_decrypts(self):
        stream = io.BytesIO(b'\x00' * 16)
        data = _decrypt_aavd(stream, KEY, IV, _translator_for(16))
        self.assertEqual(len(data), 16)


if __name__ == '__main__':
    unittest.main()
