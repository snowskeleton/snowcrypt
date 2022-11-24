import time
# hexToName = {
#     0x61617664: {
#         'name': 'aavd',
#         'func': AaxDecrypter.case_aavd
#     },
#     0x6d703461: {
#         'name': 'mp4a',
#         'func': AaxDecrypter.case_default
#     },
#     0x6d6f6f76: {
#         'name': 'moov-0',
#         'func': AaxDecrypter.case_moov
#     },
#     0x7472616b: {
#         'name': 'trak-0',
#         'func': AaxDecrypter.case_trak
#     },
#     0x6d646961: {
#         'name': 'mdia-0',
#         'func': AaxDecrypter.case_mdia
#     },
#     0x6d696e66: {
#         'name': 'minf-0',
#         'func': AaxDecrypter.case_minf
#     },
#     0x7374626c: {
#         'name': 'stbl-0',
#         'func': AaxDecrypter.case_stbl
#     },
#     0x75647461: {
#         'name': 'udta-0',
#         'func': AaxDecrypter.case_udta
#     },
#     0x6D657461: {
#         'name': 'meta-4',
#         'func': AaxDecrypter.case_meta
#     },
#     0x73747364: {
#         'name': 'stsd-8',
#         'func': AaxDecrypter.case_stsd
#     },
#     0x66747970: {
#         'name': 'ftyp-none',
#         'func': AaxDecrypter.case_ftyp
#     },
#     0x6d646174: {
#         'name': 'mdat-none',
#         'func': AaxDecrypter.case_mdat
#     },
#     0x00000000: {
#         'name': 'default',
#         'func': AaxDecrypter.case_default
#     }
# }


def avg(list: list):
    try:
        return int(sum(list) / len(list))
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


def race(funcs: list[dict], laps: int):
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
EsperoAAX = [
    'Espero_A_Silver_Ships_Novel-LC_64_22050_stereo.aax',
    'The Gathering Storm: Interview with the Narrators.m4a',
    '3bf90b36726bf44e540ea40ea34bd8df',
    '8521b45c2f75c0153bbf7ce5e2e68fdd',
]
