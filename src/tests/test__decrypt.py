import unittest
from ..snowcrypt.snowcrypt import decrypt_aax, decrypt_aaxc, deriveKeyIV
from ..snowcrypt.newcrypt import decrypt_local as newcrypt
import time


class MyTestCases(unittest.TestCase):

  def test__decrypt_local(self):
    elap = []

    def oneHundo(func, args: list, times: int):
      for _ in range(times):
        start = time.time()
        func(*args)
        end = time.time()
        elap.append(end - start)
      return sum(elap) / len(elap)

    # y = oneHundo(oldcrypt, StormAAX, 2)
    x = oneHundo(newcrypt, StormAAX, 1)
    # x = oneHundo(decrypt_local, EsperoAAX, 3)
    # self.assertEqual(x, y)
    self.assertLess(x, 0)
    # self.assertLess(x, r)


def main():
  MyTestCases().test__decrypt_local()


StormAAXC = [
    'The_Gathering_Storm_Interview_with_the_Narrators-AAX_22_64.aaxc',
    'The Gathering Storm: Interview with the Narrators.m4a',
    'edd4992ee4a03f8c83601b36468aa98b',
    '866b1fdc9fdfee5675ea40264ab78ab5',
]
StormAAX = [
    'The_Gathering_Storm_Interview_with_the_Narrators-LC_64_22050_stereo.aax',
    'The Gathering Storm: Interview with the Narrators.m4a',
    'f1c443f8db16304d24edc1245e278eaf',
    '9024b63436da4986ec5ac1f56729c0e4',
]
EsperoAAX = [
    'Espero_A_Silver_Ships_Novel-LC_64_22050_stereo.aax',
    'The Gathering Storm: Interview with the Narrators.m4a',
    '3bf90b36726bf44e540ea40ea34bd8df',
    '8521b45c2f75c0153bbf7ce5e2e68fdd',
]
