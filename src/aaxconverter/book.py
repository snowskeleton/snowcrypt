import hashlib
import json
from binascii import hexlify
from os import path

from Crypto.Cipher import AES

from .parser import arg
from .tinytag import MP4

fixedKey = bytes.fromhex('77214d4b196a87cd520045fd20a51d67')


class Book():
    def __init__(self, infile):
        self.infile = infile
        tags = MP4.get(self.infile, encoding='MP4')
        self.title = tags.title.replace(' (Unabridged)', '')
        self.outfile = self.title + '.m4a'

        try:
            self.description = tags.extra['description']
        except KeyError:
            self.description = tags.comment

        if '.aaxc' not in self.infile:
            self.key, self.iv = deriveKeyIV(tags)
        else:
            voucher = self.infile.replace('.aaxc', '.voucher')
            if not path.exists(voucher):
                raise FileNotFoundError(
                    f"Oops, {self.infile} and {voucher} not together.")

            self.key, self.iv = pullKeyIVFrom(voucher)


def pullKeyIVFrom(voucher):
    with open(voucher, 'r') as file:
        license = json.loads(file.read())[
            'content_license']['license_response']
        key = license['key']
        iv = license['iv']
        return key, iv


def deriveKeyIV(tags) -> str:
    _bytes = arg('bytes')
    hexbytes = bytes.fromhex(_bytes)
    # derive key/iv for AES cipher
    im_key = crypt(fixedKey, hexbytes)
    iv = crypt(fixedKey, im_key, hexbytes)[:16]
    key = im_key[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    data = cipher.decrypt(pad16(tags.adrmBlob))
    # make sure we're successful so far
    fileBytes = bts(data[:4])
    calculatedChecksum = crypt(key, iv)
    try:
        assert calculatedChecksum == tags.checksum
        assert swapEndien(fileBytes) == _bytes
    except:
        raise AssertionError('Either the activation bytes are incorrect'
                             ' or the audio file is invalid/corrupt.')
    # if we didn't raise any exceptions, then this file can
    # be decrypted with the provided activation_bytes

    fileKey = data[8:24]
    fileDrm = data[26:42]
    inVect = crypt(fileDrm, fileKey, fixedKey)[:16]

    return bts(fileKey), bts(inVect)


def swapEndien(string: str):
    list = [*string]
    reversed = ''
    for _ in range(int(len(list)/2)):
        x = list.pop(-1)
        y = list.pop(-1)
        reversed += y + x
    return reversed


def bts(bytes: bytes) -> str:  # bytes to string
    return str(hexlify(bytes)).strip("'")[2:]


def crypt(*bits):
    sha = hashlib.sha1()
    for b in bits:
        sha.update(b)
    return sha.digest()


def pad16(data):
    length = 16 - (len(data) % 16)
    return data + bytes([length])*length
