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
        voucherDict = json.loads(file.read())
        key = voucherDict['content_license']['license_response']['key']
        iv = voucherDict['content_license']['license_response']['iv']
        return key, iv


def deriveKeyIV(tags) -> str:
    adrmBlob = tags.adrmBlob
    _bytes = arg('bytes')
    hexbytes = bytes.fromhex(_bytes)

    # This calculated checksum should be the same
    # for every book downloaded from your Audible account.
    im_key = crypt(fixedKey, hexbytes)
    iv = crypt(fixedKey, im_key, hexbytes)[:16]
    key = im_key[:16]

    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    # pad to nearest multiple of 16
    length = 16 - (len(adrmBlob) % 16)
    adrmBlob += bytes([length])*length
    decryptedData = cipher.decrypt(adrmBlob)
    fileBytes = bts(decryptedData[:4])
    calculatedChecksum = crypt(key, iv)
    try:
        assert calculatedChecksum == tags.checksum
        assert swapEndien(fileBytes) == _bytes
    except:
        raise AssertionError('Either the activation bytes are incorrect'
                             ' or the audio file is invalid/corrupt.')

    rawKey = decryptedData[8:24]

    bval = decryptedData[26:42]
    inVect = crypt(bval, rawKey, fixedKey)[:16]

    return bts(rawKey), bts(inVect)


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
