import json
import asyncio
from os import path
from typing import Tuple

from .snowcrypt import decrypt_aaxc, key_and_iv_for_file_with_abytes
from .localExceptions import NotDecryptable, NotAnAudibleFile
from .myparser import arg
from .tinytag import MP4


def main():
    asyncio.run(othermain())


async def itter() -> str:
    for i in arg('input'):
        yield i


async def othermain():
    async for file in itter():
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

        decrypt_aaxc(
            infile,
            outfile,
            key if not arg('key') else arg('key'),
            iv if not arg('iv') else arg('iv'),
        )


def determine_key_iv(
    inpath: str,
    activation_bytes: str | None = None,
) -> Tuple:
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
