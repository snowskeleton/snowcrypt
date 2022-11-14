from binascii import hexlify
import hashlib
import sys
from os import path
import json
from Crypto.Cipher import AES
from .parser import arg
from .decrypt import decrypt_local
from .tinytag import MP4

fixedKey = bytes.fromhex('77214d4b196a87cd520045fd20a51d67')


def signal_handler(sig, frame):
    sys.exit(print('\nsnowcrypt: received SIGINT. exiting'))


def main():
    infile = arg('input')
    tags = MP4.get(infile, encoding='MP4')
    title = tags.title.replace(' (Unabridged)', '')
    outfile = title + '.m4a'

    if '.aaxc' not in infile:
        # since we don't have a voucher, we have to derive the key ourselves
        _bytes = arg('bytes')
        hexbytes = bytes.fromhex(_bytes)
        im_key = crypt(fixedKey, hexbytes)
        iv = crypt(fixedKey, im_key, hexbytes)[:16]
        key = im_key[:16]
        #decrypt drm blob to prove we can do it
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        data = cipher.decrypt(pad16(tags.adrmBlob))
        try:
            assert crypt(key, iv) == tags.checksum
            assert swapEndien(bts(data[:4])) == _bytes
        except:
            raise AssertionError('Either the activation bytes are incorrect'
                                 ' or the audio file is invalid/corrupt.')
        # if we didn't raise any exceptions, then this file can
        # be decrypted with the provided activation_bytes
        fileKey = data[8:24]
        fileDrm = data[26:42]
        inVect = crypt(fileDrm, fileKey, fixedKey)[:16]
        key, iv = bts(fileKey), bts(inVect)
    else:
        voucher = infile.replace('.aaxc', '.voucher')
        if not path.exists(voucher):
            raise FileNotFoundError(
                f"Oops, {infile} and {voucher} not together.")

        with open(voucher, 'r') as file:
            license = json.loads(file.read())[
                'content_license']['license_response']
            key, iv = license['key'], license['iv']

    decrypt_local(infile, outfile, arg('key') if arg('key')
                  else key, arg('iv') if arg('iv') else iv)


def swapEndien(string: str):
    return "".join(map(str.__add__, string[-2::-2], string[-1::-2]))


def bts(bytes: bytes) -> str:  # bytes to string
    # turns "b'string'"" into "hexstring"
    return str(hexlify(bytes)).strip("'")[2:]


def crypt(*bits):
    sha = hashlib.sha1()
    for b in bits:
        sha.update(b)
    return sha.digest()


def pad16(data):
    length = 16 - (len(data) % 16)
    return data + bytes([length])*length

if __name__ == "__main__":
    main()
