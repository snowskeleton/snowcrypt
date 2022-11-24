import unittest
import os
from ..snowcrypt.snowcrypt import decrypt_aaxc as newcrypt
from ..snowcrypt.oldcrypt import decrypt_aaxc as oldcrypt
import time


def avg(list: list):
    return sum(list) / len(list)


def now():
    return time.perf_counter_ns()


def run(func, args: list):
    start = now()
    func(*args)
    end = now()
    return end - start


def race(funcs: list[dict], laps: int):
    elap1 = []
    elap2 = []
    one = funcs[0]
    two = funcs[1]

    for _ in range(laps):
        elap1.append(run(one['func'], one['args']))
        elap2.append(run(two['func'], two['args']))

    return avg(elap1), avg(elap2)


class MyTestCases(unittest.TestCase):
    def test__decrypt_local(self):
        contestents = [{
            'func': os.system,
            'args': scSystemStormAAXC,
        }, {
            'func': os.system,
            'args': ffSystemStormAAXC
        }]
        one, two = race(contestents, 1)
        print('snowcrypt: ', str(one))
        print('ffmpeg   : ', str(two))


def main():
    MyTestCases().test__decrypt_local()


ffSystemStormAAXC = [' '.join([
    "ffmpeg",
    "-v", "quiet",
    "-audible_key",
    'edd4992ee4a03f8c83601b36468aa98b',
    "-audible_iv",
    '866b1fdc9fdfee5675ea40264ab78ab5',
    "-i",
    "The_Gathering_Storm_Interview_with_the_Narrators-AAX_22_64.aaxc",
    "-c", "copy",
    "-y",
    '"The Gathering Storm: Interview with the Narrators.m4a"',
])]

scSystemStormAAXC = [' '.join([
    'python pyi_entrypoint.py',
    'The_Gathering_Storm_Interview_with_the_Narrators-AAX_22_64.aaxc',
    'The Gathering Storm: Interview with the Narrators.m4a',
    '--key',
    'edd4992ee4a03f8c83601b36468aa98b',
    '--iv',
    '866b1fdc9fdfee5675ea40264ab78ab5',
])]

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
