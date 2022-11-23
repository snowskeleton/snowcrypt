import asyncio
import unittest
from ..snowcrypt.snowcrypt import decrypt_aaxc as newcrypt
from ..snowcrypt.oldcrypt import decrypt_aaxc as oldcrypt
import time


def avg(list: list):
  return sum(list) / len(list)


def now():
  return time.perf_counter_ns()

class MyTestCases(unittest.TestCase):

  def test__decrypt_local(self):
    elap = []

    # def makeADict():
    #   someDict = {'key': 'value'}
    #   for i in range(100000000):
    #     someDict[i] = 'literally any value'
    #   return someDict

    # someDict = makeADict()

    # def dicty():
    #   someDict['key']

    # def iffy():
    #   if 'some string' == 'some  string' \
    #           or 1 == 2 \
    #           or -2 == 2 \
    #           or 1 == 4 \
    #           or 1 == 7 \
    #           or 1 == 12 \
    #           or 1 == 9 \
    #           or 1 == 5 \
    #           or 1 == 6:
    #     pass
    # n = oneHundo(iffy, [], 100)
    # p = oneHundo(dicty, [], 100)
    # print('if  : ', n)
    # print('dict: ', p)
    # # y = oneHundo(oldcrypt, StormAAX, 2)

    def batch(func, args: list, times: int):
      for _ in range(times):
        start = now()
        func(*args)
        end = now()
        elap.append(end - start)
      return avg(elap)

    x = batch(newcrypt, StormAAX, 20)
    y = batch(oldcrypt, StormAAX, 20)
    print('new: ', x)
    print('old: ', y)


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
