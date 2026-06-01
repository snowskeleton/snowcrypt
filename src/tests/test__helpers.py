import unittest
from hashlib import sha1

from ..snowcrypt.adrm_key_derivation import _sha, _swapEndian, _pad_16
from .constants import shas


class TestSha(unittest.TestCase):
    def test_sha_known_vectors(self):
        """Verify _sha() against known SHA-1 test vectors."""
        # Skip the last two vectors (1M and 1G repetitions) for speed
        for vector in shas[:4]:
            data = bytes.fromhex(vector['hex'])
            result = _sha(data)
            expected = bytes.fromhex(vector['sha'])
            self.assertEqual(result, expected,
                             f"SHA mismatch for input '{vector['asci'][:40]}'")

    def test_sha_empty_input(self):
        result = _sha(b'')
        expected = sha1(b'').digest()
        self.assertEqual(result, expected)

    def test_sha_multiple_args_joined(self):
        """_sha() joins multiple byte arguments before hashing."""
        combined = _sha(b'abc', b'def')
        direct = sha1(b'abcdef').digest()
        self.assertEqual(combined, direct)

    def test_sha_length_truncation(self):
        """When length is specified, only that many bytes are returned."""
        result = _sha(b'test', length=16)
        full = sha1(b'test').digest()
        self.assertEqual(result, full[:16])
        self.assertEqual(len(result), 16)

    def test_sha_length_none_returns_full(self):
        result = _sha(b'test')
        self.assertEqual(len(result), 20)  # SHA-1 produces 20 bytes


class TestSwapEndian(unittest.TestCase):
    def test_swap_endian_basic(self):
        """'12345678' becomes '78563412'."""
        self.assertEqual(_swapEndian('12345678'), '78563412')

    def test_swap_endian_known_value(self):
        self.assertEqual(_swapEndian('aabbccdd'), 'ddccbbaa')

    def test_swap_endian_all_same(self):
        self.assertEqual(_swapEndian('aaaaaaaa'), 'aaaaaaaa')

    def test_swap_endian_roundtrip(self):
        """Swapping twice returns the original."""
        original = 'abcdef01'
        self.assertEqual(_swapEndian(_swapEndian(original)), original)


class TestPad16(unittest.TestCase):
    def test_pad_16_exact_multiple(self):
        """Data that's already 16 bytes gets 16 bytes of padding (0x10)."""
        data = b'\x00' * 16
        result = _pad_16(data)
        self.assertEqual(len(result), 32)
        self.assertEqual(result[16:], bytes([16]) * 16)

    def test_pad_16_needs_one_byte(self):
        """15 bytes of data gets 1 byte of padding (0x01)."""
        data = b'\x00' * 15
        result = _pad_16(data)
        self.assertEqual(len(result), 16)
        self.assertEqual(result[-1:], bytes([1]))

    def test_pad_16_general_case(self):
        """10 bytes of data gets 6 bytes of padding (0x06)."""
        data = b'A' * 10
        result = _pad_16(data)
        self.assertEqual(len(result), 16)
        self.assertEqual(result[10:], bytes([6]) * 6)

    def test_pad_16_empty_input(self):
        """Empty data gets 16 bytes of padding (0x10)."""
        result = _pad_16(b'')
        self.assertEqual(len(result), 16)
        self.assertEqual(result, bytes([16]) * 16)

    def test_pad_16_preserves_original_data(self):
        data = b'\x01\x02\x03'
        result = _pad_16(data)
        self.assertEqual(result[:3], data)


if __name__ == '__main__':
    unittest.main()
