import argparse
import os

parser = argparse.ArgumentParser(description='Argument parser description')
add = parser.add_argument
add(
    '--unattended', '-y',
    dest='unattended',
    action='store_true',
    help='Use default option for all unset values',
    default='',
)
add(
    '--activation-bytes', '-b',
    dest='abytes',
    action='store',
    help='activation_bytes override',
    default='',
)
add(
    '--extension', '-e',
    dest='extension',
    action='store',
    type=str,
    help='The output format of your audio files',
    default='mp3',
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
    '--silent', '-s',
    dest='silent',
    action='store_true',
    default=False,
    help='Suppress stdout',
)
add(
    '--library', '-l',
    dest='library',
    action='store',
    help='library filename of "audible library export" output from mkb79/audible-cli',
    default='library.tsv',
)
add(
    '--config-file-path',
    dest='config_file_path',
    action='store',
    default=os.path.expanduser('~/.aaxconverterrc'),
    help='Custom aaxconverter config file path'
)
add(
    '--add-chapters',
    dest='add_chapters',
    action='store_true',
    default=False,
    help='existence of mkb79/audible-cli generated chapters.json file'
)
args = parser.parse_args()


def arg(key):
    return vars(args)[key]
