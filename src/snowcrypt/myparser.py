import argparse

from ._version import __version__

parser = argparse.ArgumentParser(description='Argument parser description')
add = parser.add_argument
add(
    '--bytes', '-b',
    '--activation_bytes', '-activation_bytes',
    dest='bytes',
    action='store',
    help='activation bytes to decrypt AAX files',
    default=None,
)
add(
    '--bark', '-B',
    dest='bark',
    action='store_true',
    help='Print key and IV, then exit.',
    default=None,
)
add(
    'input',
    action='store',
    nargs='+',
    type=str,
    help='File(s) to convert',
    default='',
)
add(
    '--iv', '-i',
    action='store',
    type=str,
    help='AES decryption initialization vector. '
    'Used instead of voucher or key derivation.',
    default=None
)
add(
    '--jobs', '-j',
    action='store',
    dest='thread_count',
    type=int,
    default=8,
    help='the number of parallel threads to use'
)
add(
    '--key', '-k',
    action='store',
    type=str,
    help='AES decryption key. Used instead of voucher or key derivation.',
    default=None
)
add('--version',
    '-v',
    action='version',
    version='snowskeleton/snowcrypt ' + __version__)
args, _ = parser.parse_known_args()


def arg(key):
    return vars(args)[key]
