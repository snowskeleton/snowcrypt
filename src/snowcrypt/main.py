import json
import sys
from os import path

from .snowcrypt import decrypt_aaxc, deriveKeyIV
from .localExceptions import NotDecryptable
from .myparser import arg
from .tinytag import MP4


def signal_handler(sig, frame):
    sys.exit(print('\nsnowcrypt: received SIGINT. exiting'))


def main():
    infile = arg('input')
    tags = MP4.get(infile, encoding='MP4')
    title = tags.title.replace(' (Unabridged)', '')
    outfile = title + '.m4a'

    if infile.endswith('.aax'):
        _bytes = arg('bytes')
        with open(infile, 'rb') as f:
            key, iv = deriveKeyIV(f, _bytes)

    elif infile.endswith('.aaxc'):
        voucher = infile.replace('.aaxc', '.voucher')
        if not path.exists(voucher):
            raise FileNotFoundError(
                f"Oops, {infile} and {voucher} not together.")

        with open(voucher, 'r') as file:
            license = json.loads(file.read())[
                'content_license']['license_response']
            key, iv = license['key'], license['iv']

    else:
        raise NotDecryptable(
            str(infile) +
            "The file you provided doesn't end with '.aax' or '.aaxc'. " +
            "Please supply one that does.")

    decrypt_aaxc(
        infile,
        outfile,
        key if not arg('key') else arg('key'),
        iv if not arg('iv') else arg('iv'),
    )
