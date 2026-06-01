import unittest
from io import BytesIO
from struct import pack

from ..snowcrypt.snowcrypt import Translator, fshort, fint, flong, fuint, fulong


class TestFormatTuples(unittest.TestCase):
    def test_fshort_values(self):
        self.assertEqual(fshort, (">h", 2))

    def test_fint_values(self):
        self.assertEqual(fint, (">i", 4))

    def test_flong_values(self):
        self.assertEqual(flong, (">q", 8))

    def test_fuint_values(self):
        self.assertEqual(fuint, (">I", 4))

    def test_fulong_values(self):
        self.assertEqual(fulong, (">Q", 8))


class TestTranslatorConstructor(unittest.TestCase):
    def test_default_buffer_size(self):
        t = Translator()
        self.assertEqual(len(t.buf), 4096)
        self.assertEqual(t.pos, 0)
        self.assertEqual(t.wpos, 0)

    def test_custom_buffer_size(self):
        t = Translator(size=128)
        self.assertEqual(len(t.buf), 128)
        self.assertEqual(t.pos, 0)
        self.assertEqual(t.wpos, 0)


class TestReadInto(unittest.TestCase):
    def test_readInto_populates_buffer(self):
        t = Translator(size=16)
        stream = BytesIO(b'\x01\x02\x03\x04')
        n = t._readInto(stream, 4)
        self.assertEqual(n, 4)
        self.assertEqual(t.buf[:4], b'\x01\x02\x03\x04')
        self.assertEqual(t.wpos, 4)

    def test_readInto_advances_wpos(self):
        t = Translator(size=16)
        stream = BytesIO(b'\xAA\xBB\xCC\xDD\xEE\xFF\x00\x11')
        t._readInto(stream, 4)
        t._readInto(stream, 4)
        self.assertEqual(t.wpos, 8)
        self.assertEqual(t.buf[:8], b'\xAA\xBB\xCC\xDD\xEE\xFF\x00\x11')


class TestNext(unittest.TestCase):
    def test_next_reads_from_buffer(self):
        t = Translator(size=16)
        # Place a big-endian int value 42 at position 0
        t.buf[0:4] = pack(">i", 42)
        t.wpos = 4
        result = t.next(fint)
        self.assertEqual(result, 42)
        self.assertEqual(t.pos, 4)

    def test_next_advances_position(self):
        t = Translator(size=16)
        t.buf[0:4] = pack(">i", 100)
        t.buf[4:8] = pack(">i", 200)
        t.wpos = 8
        first = t.next(fint)
        second = t.next(fint)
        self.assertEqual(first, 100)
        self.assertEqual(second, 200)
        self.assertEqual(t.pos, 8)


class TestReadOne(unittest.TestCase):
    def test_readOne_fint(self):
        stream = BytesIO(pack(">i", -1))
        t = Translator(size=16)
        result = t.readOne(fint, stream)
        self.assertEqual(result, -1)

    def test_readOne_fshort(self):
        stream = BytesIO(pack(">h", 32000))
        t = Translator(size=16)
        result = t.readOne(fshort, stream)
        self.assertEqual(result, 32000)

    def test_readOne_flong(self):
        stream = BytesIO(pack(">q", 2**40))
        t = Translator(size=16)
        result = t.readOne(flong, stream)
        self.assertEqual(result, 2**40)

    def test_readOne_fuint(self):
        """Unsigned format returns positive for large values."""
        value = 0x80000001
        stream = BytesIO(pack(">I", value))
        t = Translator(size=16)
        result = t.readOne(fuint, stream)
        self.assertGreater(result, 0)
        self.assertEqual(result, value)


class TestReadAtomSize(unittest.TestCase):
    def test_readAtomSize_small(self):
        """Values below 0x80000000 parse correctly as positive."""
        size = 0x1000
        stream = BytesIO(pack(">I", size))
        t = Translator()
        result = t.readAtomSize(stream)
        self.assertEqual(result, size)

    def test_readAtomSize_large(self):
        """Values >= 0x80000000 stay positive with unsigned format (PR #12 fix)."""
        size = 0x80000001  # 2 GiB + 1
        stream = BytesIO(pack(">I", size))
        t = Translator()
        result = t.readAtomSize(stream)
        self.assertGreater(result, 0)
        self.assertEqual(result, size)

    def test_readAtomSize_extended_64bit(self):
        """When 4-byte size == 1, reads the 8-byte extended size."""
        extended_size = 0x1_0000_0000  # 4 GiB
        data = pack(">I", 1) + pack(">Q", extended_size)
        stream = BytesIO(data)
        t = Translator()
        result = t.readAtomSize(stream)
        self.assertEqual(result, extended_size)

    def test_readAtomSize_typical_mp4_sizes(self):
        """Typical MP4 atom sizes (a few KB to a few MB) parse correctly."""
        for size in [8, 256, 4096, 1_000_000, 0x7FFFFFFF]:
            stream = BytesIO(pack(">I", size))
            t = Translator()
            result = t.readAtomSize(stream)
            self.assertEqual(result, size, f"Failed for size {size}")


class TestWrite(unittest.TestCase):
    def test_write_outputs_buffer(self):
        t = Translator(size=16)
        t.buf[0:4] = b'\xDE\xAD\xBE\xEF'
        t.wpos = 4
        out = BytesIO()
        written = t.write(out)
        self.assertEqual(written, 4)
        out.seek(0)
        self.assertEqual(out.read(), b'\xDE\xAD\xBE\xEF')

    def test_write_empty_buffer(self):
        t = Translator(size=16)
        out = BytesIO()
        written = t.write(out)
        self.assertEqual(written, 0)
        out.seek(0)
        self.assertEqual(out.read(), b'')


if __name__ == '__main__':
    unittest.main()
