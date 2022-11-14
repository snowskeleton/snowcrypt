import argparse

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
    'input',
    action='store',
    type=str,
    help='File to be converted',
    default='',
)
args, unknown = parser.parse_args()


def arg(key):
    return vars(args)[key]
