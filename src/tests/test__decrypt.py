import sys
import filecmp
import unittest
import os
from ..snowcrypt.snowcrypt import decrypt_aaxc as newcrypt
from ..snowcrypt.oldcrypt import decrypt_aaxc as oldcrypt
import time
import cProfile
import pstats

from .longvars import *

contestents = [{
    'func': newcrypt,
    'args': StormAAXC,
}, {
    'func': oldcrypt,
    'args': ControlStormAAXC
}]

file1 = contestents[0]['args'][1]
file2 = contestents[1]['args'][1]


class MyTestCases(unittest.TestCase):
    def test__decrypt_local(self):
        # profile = cProfile.Profile()
        # profile.runcall(run, contestents[0]['func'], contestents[0]['args'])
        # ps = pstats.Stats(profile)
        # ps.print_stats()
        # sys.exit()
        # num = 0
        # print(run(contestents[num]['func'], contestents[num]['args']))
        one, two = race(contestents, 10)
        print('new : ', str(one)[:3])
        print('old : ', str(two)[:3])
        print('new : ', str(one))
        print('old : ', str(two))
        assert filecmp.cmp(file1, file2)


def main():
    MyTestCases().test__decrypt_local()
