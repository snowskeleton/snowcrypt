import unittest
from ..snowcrypt.snowcrypt import decrypt_aaxc as newcrypt
from ..snowcrypt.oldcrypt import decrypt_aaxc as oldcrypt
import time


def avg(list: list):
    return sum(list) / len(list)


def now():
    return time.perf_counter_ns()


def _some(func, args: list):
    start = now()
    func(*args)
    end = now()
    return end - start


def race(funcs: list[dict], laps: int):
    elap = []
    elap2 = []
    one = funcs[0]
    two = funcs[1]

    for _ in range(laps):
        elap.append(_some(one['func'], one['args']))
        elap2.append(_some(two['func'], two['args']))

    return avg(elap), avg(elap2)


class MyTestCases(unittest.TestCase):
    def test__decrypt_local(self):

        contestents = [
            {
                # 'func': oldcrypt,
                'func': newcrypt,
                'args': StormAAXC,
                # 'args': EsperoAAX,
            },
            {
                'func': oldcrypt,
                # 'func': newcrypt,
                'args': StormAAXC,
                # 'args': EsperoAAX,
            }
        ]
        one, two = race(contestents, 5)
        print('new: ', str(one)[:3])
        print('old: ', str(two)[:3])


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
