import argparse

parser = argparse.ArgumentParser(description='Argument parser description')
add = parser.add_argument
add(
    '--activation-bytes', '-b',
    dest='abytes',
    action='store',
    help='activation_bytes override',
    default='',
)
add('--dir', '-d',
    dest='outputDir',
    action='store',
    default='.',
    help='Directy in which to place the output file',
    )
add(
    '--extension', '-e', '-f',
    dest='extension',
    action='store',
    type=str,
    help='The output format of your audio files',
    default='m4a',
)
add(
    '--input', '-i',
    dest='input',
    action='store',
    type=str,
    help='File to be converted',
    default='',
)
add(
    '--output', '-o',
    dest='output',
    type=str,
    action='store',
    help='Output filename. Accepts pattern or explicit string. Defaults to filename without junk.',
    default='output',
)
add(
    '--overwrite',
    dest='overwrite',
    choices=['y', 'n'],
    help='Use default option for all unset values',
    default='y',
)
args = parser.parse_args()


def arg(key):
    return vars(args)[key]
