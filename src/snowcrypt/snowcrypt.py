# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
from struct import unpack_from, pack_into
from os import path
from hashlib import sha1
from io import BufferedReader, BufferedWriter

from Crypto.Cipher.AES import MODE_CBC, new as newAES
from binascii import hexlify

from .localExceptions import CredentialMismatch
from .constants import *


fshort, fint, flong = (">h", 2), (">i", 4), (">q", 8)


class Translator:
    def __init__(self, size: int = None):
        self.buf = bytearray(size if size != None else 4096)
        self.pos, self.wpos = 0, 0

    def next(self, format: tuple):
        data = unpack_from(format[0], self.buf, self.pos)[0]
        self.pos += format[1]
        return data

    def readOne(self, format: tuple, inStream: BufferedReader):
        length = format[1]
        self._readInto(inStream, length)
        r = self.next(format)
        return r

    def _readInto(self, inStream: BufferedReader, length: int or None) -> int:
        start = self.wpos
        self.buf[start:start + length] = inStream.read(length)
        self.wpos += length
        return length

    def write(self, out: BufferedWriter) -> int:
        end = self.wpos
        data = self.buf[0:end]
        out.write(data)
        return self.wpos

    def readAtomSize(self, inStream: BufferedReader) -> int:
        atomLength = self.readOne(fint, inStream)
        return atomLength if atomLength != 1 else self.readOne(flong, inStream)


def _decrypt_aavd(inStream: BufferedReader, key, iv, t: Translator):
    # setup
    length = t.next(fint)
    aes = newAES(key, MODE_CBC, iv=iv)

    # for cipher padding, (up to) last 2 bytes are unencrypted
    encryptedLength = length & 0xFFFFFFF0
    unencryptedLength = length & 0x0000000F

    encryptedData = inStream.read(encryptedLength)
    unencryptedData = inStream.read(unencryptedLength)

    return aes.decrypt(encryptedData) + unencryptedData


def _meta_mask(inStream, outStream, length, t, **_):
    t.readOne(fint, inStream)
    t.write(outStream)
    _atomizer(inStream, outStream, length)


def _stsd_mask(inStream, outStream, length, t, **_):
    t.readOne(flong, inStream)
    t.write(outStream)
    _atomizer(inStream, outStream, length)


def _aavd_mask(inStream, outStream, length, t, atomPosition=None, **_):
    # change container name so MP4 readers don't complain
    pack_into(fint[0], t.buf, atomPosition, MP4A)
    length -= t.write(outStream)
    outStream.write(inStream.read(length))


def _default_mask(inStream, outStream, length, t, **_):
    t.write(outStream)
    _atomizer(inStream, outStream, length)


def _just_copy_it(inStream, outStream, length, t, **_):
    length -= t.write(outStream)
    outStream.write(inStream.read(length))


def _ftyp_writer(inStream, outStream, length, t, **_):
    length -= t.write(outStream)
    buf = bytearray(length)
    pos = 0
    for tag in FTYP_TAGS:
        pack_into(fint[0], buf, pos, tag)
        pos += 4
    for i in range(24, length):
        buf[i] = 0
    outStream.write(buf)
    inStream.read(length)


def _mdat_writer(inStream, outStream, length, t, key=None, iv=None, atomEnd=None, **_):
    # this is the main work horse
    t.write(outStream)
    while inStream.tell() < atomEnd:
        t = Translator()
        atomLength = t.readAtomSize(inStream)
        atomTypePosition = t.pos
        atomType = t.readOne(fint, inStream)

        # after the atom type comes 5 additional fields describing the data.
        # We only care about the last two.
        # skip (in order) time (in ms), first block index,
        # trak number, overall block size, block count
        t.readOne(fint, inStream)
        t.readOne(fint, inStream)
        t.readOne(fint, inStream)
        totalBlockSize = t.readOne(fint, inStream)
        blockCount = t.readOne(fint, inStream)

        # next come the atom specific fields
        # aavd has a list of sample sizes and then the samples.
        if atomType == AAVD:
            # replace aavd type with mp4a type
            pack_into(fint[0], t.buf,  atomTypePosition, MP4A)
            t._readInto(inStream, blockCount * 4)
            t.write(outStream)

            for _ in range(blockCount):
                outStream.write(_decrypt_aavd(inStream, key, iv, t))

        else:
            length = t.write(outStream)
            outStream.write(inStream.read(
                atomLength + totalBlockSize - length))


_atomFuncs = {
    FTYP: _ftyp_writer,
    MDAT: _mdat_writer,
    AAVD: _aavd_mask,
    META: _meta_mask,
    STSD: _stsd_mask,
    MOOV: _default_mask,
    TRAK: _default_mask,
    MDIA: _default_mask,
    MINF: _default_mask,
    STBL: _default_mask,
    UDTA: _default_mask,
}


def _atomizer(
    inStream: BufferedReader = None,
    outStream: BufferedWriter = None,
    eof: int = None,
    key=None,
    iv=None
):
    while inStream.tell() < eof:
        t = Translator()
        atomStart = inStream.tell()
        length = t.readAtomSize(inStream)
        atomEnd = atomStart + length
        atomPosition = t.pos
        atomType = t.readOne(fint, inStream)

        func = _atomFuncs.get(atomType, _just_copy_it)
        func(
            atomPosition=atomPosition,
            outStream=outStream,
            inStream=inStream,
            atomEnd=atomEnd,
            length=length,
            key=key,
            iv=iv,
            t=t,
        )


def _decrypt(inStream: BufferedReader, outStream: BufferedWriter, key: bytes, iv: bytes):
    _atomizer(inStream, outStream, path.getsize(inStream.name), key, iv)


def decrypt_aaxc(inpath: str, outpath: str, key: int, iv: int):
    """converts inpath with key and iv, writing to outpath

    Args:
        inpath (str): source
        outpath (str): destination
        key (int): AES key
        iv (int): AES initialization vector
    """
    key = bytes.fromhex(key)
    iv = bytes.fromhex(iv)
    with open(inpath, 'rb') as src:
        with open(outpath, 'wb') as dest:
            _decrypt(src, dest, key, iv)


def decrypt_aax(inpath: str, outpath: str, activation_bytes: str):
    """convenience function for deriving AES key and initialization vector,
    then decrypting with those values.

    Args:
        inpath (str): file path to input
        outpath (str): file path to output
        activation_bytes (str): decryption bytes unique to your account
    """
    with open(inpath, 'rb') as inStream:
        key, iv = deriveKeyIV(inStream, activation_bytes)
    decrypt_aaxc(inpath, outpath, key, iv)


def deriveKeyIV(inStream: BufferedReader, activation_bytes: str):
    """derive key and initialization vector for given BufferReader

    Args:
        inStream (BufferedReader): open file stream
        activation_bytes (str): decryption bytes unique to your account

    Returns:
        tuple[str, str]: key, initialization vector
    """
    file_start = inStream.tell()
    im_key = _sha(FIXEDKEY, bytes.fromhex(activation_bytes))
    iv = _sha(FIXEDKEY, im_key, bytes.fromhex(activation_bytes), length=16)
    key = im_key[:16]

    inStream.seek(ADRM_START)
    cipher = newAES(key, MODE_CBC, iv=iv)
    data = cipher.decrypt(_pad_16(inStream.read(ADRM_LENGTH)))

    inStream.seek(CKSM_START)
    real_checksum = inStream.read(CKSM_LENGTH)
    derived_checksum = _sha(key, iv)
    validDrmChecksum = derived_checksum == real_checksum

    real_bites = _swapEndian(_bts(data[:4]))
    activation_bytes_match = real_bites == activation_bytes
    if not validDrmChecksum or not activation_bytes_match:
        raise CredentialMismatch('Either the activation bytes are incorrect'
                                 ' or the audio file is invalid or corrupt.')
    fileKey = _key_mask(data)
    fileDrm = _drm_mask(data)
    inVect = _sha(fileDrm, fileKey, FIXEDKEY, length=16)
    inStream.seek(file_start)
    return _bts(fileKey), _bts(inVect)


def _key_mask(data: bytes):
    return data[8:24]


def _drm_mask(data: bytes):
    return data[26:42]


def _swapEndian(string: str):
    """turns 12345678 into 78563412
    """
    return "".join(map(str.__add__, string[-2::-2], string[-1::-2]))


def _bts(bytes: bytes) -> str:
    return str(hexlify(bytes)).strip("'")[2:]


def _sha(*bits: bytes, length: int = None):
    return sha1(b''.join(bits)).digest()[:length]


def _pad_16(data: bytes, length: int = 16) -> bytes:
    length = length - (len(data) % length)
    return data + bytes([length])*length
