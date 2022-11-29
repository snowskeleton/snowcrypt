import filecmp
import unittest
from ..snowcrypt.snowcrypt import decrypt_aaxc as newcrypt
from ..snowcrypt.oldcrypt import decrypt_aaxc as oldcrypt

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
            # TODO: implement scalene profiler
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


def main():
    MyTestCases().test__decrypt_local()

# b = bytes.fromhex
# key = b('9dc2c84a37850c11699818605f47958c')
# iv = b('256953b2feab2a04ae0180d8335bbed6')
# plainText = b('2e586692e647f5028ec6fa47a55a2aab')
# cipherText = b('1b1ebd1fc45ec43037fd4844241a437f')
# from ..snowcrypt.aes import AES
# aes = AES(key)
# testing = aes.decrypt_cbc(cipherText, iv)
# assert testing == plainText
