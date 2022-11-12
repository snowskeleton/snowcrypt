import hashlib
import json
from binascii import hexlify
from dataclasses import dataclass, field
from os import path

from Crypto.Cipher import AES

from .parser import arg
from .tinytag import MP4

fixedKey = bytes.fromhex('77214d4b196a87cd520045fd20a51d67')
@dataclass
class Book():

    infile: str
    iv: str = field(init=False)
    key: str = field(init=False)
    title: str = field(init=False)
    outfile: str = field(init=False)
    description: str = field(init=False)

    def __post_init__(self):
        self.tags = MP4.get(self.infile, encoding='MP4')
        self.title = self.tags.title.replace(' (Unabridged)', '')
        self.outfile = self.title + '.m4a'

        try:
            self.description = self.tags.extra['description']
        except KeyError:
            self.description = self.tags.comment

        if '.aaxc' not in self.infile:
            self.key, self.iv = deriveKeyAndIV(self)
        else:
            voucher = self.infile.replace('.aaxc', '.voucher')
            if not path.exists(voucher):
                raise FileNotFoundError(
                    f"Oops, {self.infile} and {voucher} not together.")

            self.key, self.iv = aaxcExtrasFrom(voucher)


def aaxcExtrasFrom(voucher):
    with open(voucher, 'r') as file:
        voucherDict = json.loads(file.read())
        key = voucherDict['content_license']['license_response']['key']
        iv = voucherDict['content_license']['license_response']['iv']
        return key, iv


def deriveKeyAndIV(book: Book) -> str:
    adrmBlob = book.tags.adrmBlob
    _bytes = arg('bytes')
    hexbytes = bytes.fromhex(_bytes)

    # This calculated checksum should be the same
    # for every book downloaded from your Audible account.
    im_key = crypt(fixedKey, hexbytes)
    im_iv = crypt(fixedKey, im_key, hexbytes)[:16]
    im_key = im_key[:16]
    calculatedChecksum = crypt(im_key, im_iv)

    if calculatedChecksum != book.tags.checksum:
        raise AssertionError('Computed checksum != file checksum. '
                             'Either the activation bytes are incorrect, '
                             'or the audio file is invalid/corrupt.')
    cipher = AES.new(im_key, AES.MODE_CBC, iv=im_iv)
    # pad to nearest multiple of 16
    length = 16 - (len(adrmBlob) % 16)
    adrmBlob += bytes([length])*length
    decryptedData = cipher.decrypt(adrmBlob)
    fileBytes = bts(decryptedData[:4])
    if swapEndien(fileBytes) != _bytes:
        raise Exception(
            f'Unable to decrypt file with provided activation_bytes: {_bytes}'
        )
    rawKey = decryptedData[8:24]

    bval = decryptedData[26:42]
    inVect = crypt(bval, rawKey, fixedKey)[:16]

    return bts(rawKey), bts(inVect)


def swapEndien(string: str):
    # adrmBlob is big endien, so we need to reverse it
    list = [*string]
    reversed = ''
    for _ in range(int(len(list)/2)):
        x = list.pop(-1)
        y = list.pop(-1)
        reversed += y + x
    return reversed


def bts(bytes: bytes) -> str:  # bytes to string
    string = hexlify(bytes)
    return str(string).strip("'")[2:]


def crypt(*bits):
    sha = hashlib.sha1()
    for b in bits:
        sha.update(b)
    return sha.digest()
