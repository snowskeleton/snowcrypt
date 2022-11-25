import sys
import signal
import os
import filecmp
import unittest
import os
from ..snowcrypt.snowcrypt import decrypt_aaxc as newcrypt
from ..snowcrypt.oldcrypt import decrypt_aaxc as oldcrypt
import time
import cProfile
import pstats

from .longvars import *
from ..snowcrypt.localExceptions import NotDecryptable


def handler(*_):
    raise NotDecryptable()

contestents = [{
    'func': newcrypt,
    # 'args': StormAAXC,
    'args': EsperoAAX,
}, {
    'func': oldcrypt,
    # 'args': ControlStormAAXC,
    'args': ControlEsperoAAX,
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
        try:
            signal.signal(signal.SIGALRM, handler)
            signal.alarm(60)
            one, two = race(contestents, 1)
            assert filecmp.cmp(file1, file2)
            one = str(one)[:5]
            two = str(two)[:5]
            print('new : ', one)
            print('old : ', two)
        except AssertionError:
            print('Files are not the same')
        except NotDecryptable:
            print('Decryption took too long')
        except KeyboardInterrupt:
            print('\nReceived escape sequence')
        finally:
            signal.alarm(0)          # Disable the alarm


def main():
    MyTestCases().test__decrypt_local()
