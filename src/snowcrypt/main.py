import json
import logging

from os import path
from datetime import datetime
from typing import Tuple

from .adrm_key_derivation import key_and_iv_for_file_with_abytes
from .snowcrypt import decrypt_aaxc
from .localExceptions import NotDecryptable, NotAnAudibleFile
from .myparser import arg
from .tinytag import MP4

from multiprocessing import Pool


def helper(input):
    infile, _, _, _ = [*input]
    logging.info(f"Starting: {infile}")
    then = datetime.now()
    decrypt_aaxc(*input)
    now = datetime.now()
    delta = now - then
    if delta.seconds != 0:
        delta = delta.seconds
    else:
        delta = delta.microseconds
    fraction = delta / path.getsize(infile)
    logging.info(f"Finished: {infile}. Total seconds: {fraction}")


def main():
    iterables = [
        [*_get_args_for(file)]
        for file in arg('input')
    ]
    with Pool(arg('thread_count')) as pool:
        pool.map(helper, iterables)


def _get_args_for(file) -> list:
    infile: str = file
    if not isaax(infile) and not isaaxc(infile):
        raise NotAnAudibleFile(
            infile +
            "The file you provided doesn't end with '.aax' or '.aaxc'. " +
            "Please supply one that does.")

    key, iv = determine_key_iv(
        infile,
        arg('bytes') if isaax(infile) else None,
    )

    tags = MP4.get(infile, encoding='MP4')
    title = tags.title.replace(' (Unabridged)', '')
    outfile = title + '.m4a'

    return [infile, outfile, key, iv]


def determine_key_iv(
    inpath: str,
    activation_bytes: str | None = None,
) -> Tuple:
    if arg('key') and arg('iv'):
        return arg('key'), arg('iv')

    if isaax(inpath):
        activation_bytes = arg('bytes')
        if not activation_bytes:
            raise NotDecryptable(
                'Must supply activation_bytes to decrypt .aax')

        return key_and_iv_for_file_with_abytes(inpath, activation_bytes)

    voucher = inpath.replace('.aaxc', '.voucher')
    if not path.exists(voucher):
        raise FileNotFoundError(
            f"Oops, {inpath} and {voucher} not together.")

    with open(voucher, 'r') as file:
        license = json.loads(file.read())[
            'content_license']['license_response']
        return license['key'], license['iv']


def isaaxc(file) -> bool: return file.endswith('.aaxc')


def isaax(file) -> bool: return file.endswith('.aax')
