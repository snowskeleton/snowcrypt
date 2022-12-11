import time
from typing import List


def avg(list: list):
    try:
        list.sort()
        if len(list) > 3:
            list.pop(0)
            list.pop(-1)
        s = max(list)
        list = [float(i)/s for i in list]
        return sum(list) / len(list)
    except ZeroDivisionError:
        return 0


def now():
    return time.perf_counter_ns()


def run(func, args: list):
    start = 0
    end = 0
    start = now()
    func(*args)
    end = now()
    return end - start


def race(funcs: List[dict], laps: int):
    elap1 = []
    elap2 = []
    one = funcs[0]
    two = funcs[1]

    for _ in range(laps):
        elap1.append(run(one['func'], one['args']))
        elap2.append(run(two['func'], two['args']))

    return avg(elap1), avg(elap2)


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
])]

ControlStormAAXC = [
    'The_Gathering_Storm_Interview_with_the_Narrators-AAX_22_64.aaxc',
    'The Gathering Storm: Interview with the Narrators-control.m4a',
    'edd4992ee4a03f8c83601b36468aa98b',
    '866b1fdc9fdfee5675ea40264ab78ab5',
]
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
ControlEsperoAAX = [
    'Espero_A_Silver_Ships_Novel-LC_64_22050_stereo.aax',
    'The Gathering Storm: Interview with the Narrators-control.m4a',
    '3bf90b36726bf44e540ea40ea34bd8df',
    '8521b45c2f75c0153bbf7ce5e2e68fdd',
]
EsperoAAX = [
    'Espero_A_Silver_Ships_Novel-LC_64_22050_stereo.aax',
    'The Gathering Storm: Interview with the Narrators.m4a',
    '3bf90b36726bf44e540ea40ea34bd8df',
    '8521b45c2f75c0153bbf7ce5e2e68fdd',
]

shas = [
    {
        'asci': 'abc',
        'hex': '616263',
        'sha': 'a9993e364706816aba3e25717850c26c9cd0d89d',
    },
    {
        'asci': '',
        'hex': '',
        'sha': 'da39a3ee5e6b4b0d3255bfef95601890afd80709',
    },
    {
        'asci': 'abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq',
        'hex': '6162636462636465636465666465666765666768666768696768696A68696A6B696A6B6C6A6B6C6D6B6C6D6E6C6D6E6F6D6E6F706E6F7071',
        'sha': '84983e441c3bd26ebaae4aa1f95129e5e54670f1',
    },
    {
        'asci': 'abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmnoijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu',
        'hex': '61626364656667686263646566676869636465666768696A6465666768696A6B65666768696A6B6C666768696A6B6C6D6768696A6B6C6D6E68696A6B6C6D6E6F696A6B6C6D6E6F706A6B6C6D6E6F70716B6C6D6E6F7071726C6D6E6F707172736D6E6F70717273746E6F707172737475',
        'sha': 'a49b2446a02c645bf419f995b67091253a04a259',
    },
    {
        'asci': 'a' * 1000000,  # one million
        'hex': '61' * 1000000,
        'sha': '34aa973cd4c4daa4f61eeb2bdbad27316534016f',
    },
    {
        'asci': 'abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmno' * 16777216,  # one million
        'hex': '61626364656667686263646566676869636465666768696A6465666768696A6B65666768696A6B6C666768696A6B6C6D6768696A6B6C6D6E68696A6B6C6D6E6F' * 16777216,  # 2^33, 1GB
        'sha': '7789f0c9ef7bfc40d93311143dfbe69e2017f592',
    }
]

TEST_BYTES = 'abcdef01'


class EncryptionFailure(Exception):
    pass


class SignificantTimeDifference(Exception):
    pass
