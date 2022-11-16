import hashlib
import json
import sys
from binascii import hexlify
from os import path

from Crypto.Cipher import AES

from .decrypt import decrypt_local
from .localExceptions import *
from .parser import arg
from .tinytag import MP4

fixedKey = bytes.fromhex('77214d4b196a87cd520045fd20a51d67')


def signal_handler(sig, frame):
    sys.exit(print('\nsnowcrypt: received SIGINT. exiting'))


def main():
    infile = arg('input')
    tags = MP4.get(infile, encoding='MP4')
    title = tags.title.replace(' (Unabridged)', '')
    outfile = title + '.m4a'

    if infile.endswith('.aax'):
        # derive AES key and iv
        _bytes = arg('bytes')
        im_key = crypt(fixedKey, bytes.fromhex(_bytes))
        iv = crypt(fixedKey, im_key, bytes.fromhex(_bytes))[:16]
        key = im_key[:16]
        # decrypt drm blob to prove we can do it
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        data = cipher.decrypt(pad(tags.adrmBlob, 16))
        try:
            assert crypt(key, iv) == tags.checksum
            assert swapEndien(bts(data[:4])) == _bytes
        except:
            raise CredentialMismatch('Either the activation bytes are incorrect'
                                     ' or the audio file is invalid or corrupt.')
        # if we didn't raise any exceptions, then this file can
        # be decrypted with the provided activation_bytes
        fileKey = data[8:24]
        fileDrm = data[26:42]
        inVect = crypt(fileDrm, fileKey, fixedKey)[:16]
        key, iv = bts(fileKey), bts(inVect)

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
            "The file you provided doesn't end with '.aax' or '.aaxc'." +
            "Please supply one that does.")

    if arg('bark'):
        sys.exit(print(f'* key *\n{key}\n* iv *\n{iv}'))
    decrypt_local(
        infile,
        outfile,
        arg('key') if arg('key') else key,
        arg('iv') if arg('iv') else iv,
    )


def swapEndien(string: str):
    return "".join(map(str.__add__, string[-2::-2], string[-1::-2]))


def bts(bytes: bytes) -> str:
    # turns "b'bytes'"" into "hexstring"
    return str(hexlify(bytes)).strip("'")[2:]


def crypt(*bits: bytes):
    return hashlib.sha1(b''.join(bits)).digest()


def pad(data: bytes, length: int = 16) -> bytes:
    l = length - (len(data) % length)
    return data + bytes([l])*l


if __name__ == "__main__":
    main()
