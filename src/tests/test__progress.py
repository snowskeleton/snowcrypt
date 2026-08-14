import io
import unittest

from ..snowcrypt.snowcrypt import _ProgressWriter


class TestProgressWriter(unittest.TestCase):
    def _writer(self, interval, total=1000):
        self.reports = []
        self.sink = io.BytesIO()
        return _ProgressWriter(
            self.sink,
            lambda written, size: self.reports.append((written, size)),
            total,
            interval,
        )

    def test_data_reaches_the_underlying_stream(self):
        writer = self._writer(interval=10)
        writer.write(b'hello ')
        writer.write(b'world')
        self.assertEqual(self.sink.getvalue(), b'hello world')

    def test_write_returns_underlying_count(self):
        writer = self._writer(interval=10)
        self.assertEqual(writer.write(b'abcd'), 4)

    def test_reports_once_per_interval(self):
        writer = self._writer(interval=100)
        for _ in range(10):
            writer.write(b'x' * 30)
        # 300 bytes written, reported at every 100-byte boundary crossing.
        self.assertEqual(
            self.reports,
            [(120, 1000), (240, 1000)],
        )

    def test_no_report_below_interval(self):
        writer = self._writer(interval=1024)
        writer.write(b'x' * 100)
        self.assertEqual(self.reports, [])

    def test_reports_are_cumulative(self):
        writer = self._writer(interval=1)
        writer.write(b'ab')
        writer.write(b'cd')
        self.assertEqual([r[0] for r in self.reports], [2, 4])

    def test_total_is_passed_through(self):
        writer = self._writer(interval=1, total=4242)
        writer.write(b'x')
        self.assertEqual(self.reports[0][1], 4242)

    def test_written_property_tracks_every_write(self):
        """Not just the reported ones — used for the final callback."""
        writer = self._writer(interval=1_000_000)
        writer.write(b'x' * 50)
        writer.write(b'y' * 25)
        self.assertEqual(writer.written, 75)
        self.assertEqual(self.reports, [])

    def test_zero_interval_does_not_divide_by_zero(self):
        writer = self._writer(interval=0)
        writer.write(b'x')
        self.assertEqual(len(self.reports), 1)

    def test_attributes_pass_through_to_the_stream(self):
        """Atom handlers call tell() and name on the stream directly."""
        writer = self._writer(interval=10)
        writer.write(b'abc')
        self.assertEqual(writer.tell(), 3)

    def test_callback_exceptions_propagate(self):
        def boom(written, total):
            raise RuntimeError('callback failed')

        writer = _ProgressWriter(io.BytesIO(), boom, 100, 1)
        with self.assertRaises(RuntimeError):
            writer.write(b'x')


if __name__ == '__main__':
    unittest.main()
