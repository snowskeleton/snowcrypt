import unittest

# https://www.di-mgt.com.au/sha_testvectors.html


class MyTestCases(unittest.TestCase):
  def test__snowsha(self):
    from ..snowcrypt.snowcrypt import _sha, _bts
    from .constants import shas
    for sha in shas:
      h = sha['asci'].encode('utf-8')
      mix = _sha(h)
      self.assertEqual(_bts(mix), sha['sha'])
