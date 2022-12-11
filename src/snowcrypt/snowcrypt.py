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

    def _next(self, format: tuple):
        return unpack_from(format[0], self.buf, self.pos)[0]

    def _readOne(self, format: tuple, inStream: BufferedReader):
        length = format[1]
        self._readInto(inStream, length)
        r = self._next(format)
        self.pos += length
        return r

    def _readInto(self, inStream: BufferedReader, length: int | None) -> int:
        start = self.wpos
        end = start + length
        self.buf[start:end] = inStream.read(length)
        self.wpos += length
        return length

    def _write(self, inStream, out: BufferedWriter) -> int:
        data = inStream[0: self.wpos]
        out.write(data)
        return self.wpos

    def _readAtomSize(self, inStream: BufferedReader) -> int:
        atomLength = self._readOne(fint, inStream)
        return atomLength if atomLength != 1 else self._readOne(flong, inStream)

    def _fillFtyp(self, inStream: BufferedReader, remaining: int, outStream: BufferedWriter):
        length = remaining
        self._readInto(inStream, remaining)
        self.wpos += length
        buf = bytearray(remaining)
        pack_into(fint[0], buf, 0,  M4A)
        pack_into(fint[0], buf, 4,  VERSION2_0)
        pack_into(fint[0], buf, 8,  ISO2)
        pack_into(fint[0], buf, 12, M4B)
        pack_into(fint[0], buf, 16, MP42)
        pack_into(fint[0], buf, 20, ISOM)
        for i in range(24, length):
            buf[i] = 0
        self._write(buf, outStream)


def _decrypt(inStream: BufferedReader, outStream: BufferedWriter, key: bytes, iv: bytes):
    def walk_mdat(endPosition: int):  # samples
        while inStream.tell() < endPosition:
            t = Translator()
            atomLength = t._readAtomSize(inStream)
            atomTypePosition = t.pos
            atomType = t._readOne(fint, inStream)

            # after the atom type comes 5 additional fields describing the data.
            # We only care about the last two.
            # skip time in ms, first block index, trak number, overall block size, block count
            t._readOne(fint, inStream)
            t._readOne(fint, inStream)
            t._readOne(fint, inStream)
            totalBlockSize = t._readOne(fint, inStream)
            blockCount = t._readOne(fint, inStream)  # number of blocks

            # next come the atom specific fields
            # aavd has a list of sample sizes and then the samples.
            if atomType == AAVD:
                # replace aavd type with mp4a type
                pack_into(fint[0], t.buf,  atomTypePosition, MP4A)
                t._readInto(inStream, blockCount * 4)
                t._write(t.buf, outStream)

                for _ in range(blockCount):
                    # setup
                    sampleLength = t._next(fint)
                    t.pos += fint[1]
                    aes = newAES(key, MODE_CBC, iv=iv)

                    # for cipher padding, (up to) last 2 bytes are unencrypted
                    encryptedLength = sampleLength & 0xFFFFFFF0
                    unencryptedLength = sampleLength & 0x0000000F

                    encryptedData = inStream.read(encryptedLength)
                    unencryptedData = inStream.read(unencryptedLength)

                    outStream.write(aes.decrypt(encryptedData))
                    outStream.write(unencryptedData)

            else:
                length = t._write(t.buf, outStream)
                _copy(inStream, atomLength +
                      totalBlockSize - length, outStream)

    def walk_atoms(endPosition: int):  # everything
        while inStream.tell() < endPosition:
            t = Translator()
            atomStart = inStream.tell()
            atomLength = t._readAtomSize(inStream)
            atomEnd = atomStart + atomLength
            atomPosition = t.pos
            atomType = t._readOne(fint, inStream)

            remaining = atomLength

            if atomType == FTYP:
                remaining -= t._write(t.buf, outStream)
                t.pos, t.wpos = 0, 0
                t._fillFtyp(inStream, remaining, outStream)
            elif atomType == META:
                t._readInto(inStream, 4)
                t._write(t.buf, outStream)
                walk_atoms(atomEnd)
            elif atomType == STSD:
                t._readInto(inStream, 8)
                t._write(t.buf, outStream)
                walk_atoms(atomEnd)
            elif atomType == MDAT:
                t._write(t.buf, outStream)
                walk_mdat(atomEnd)
            elif atomType == AAVD:
                pack_into(fint[0], t.buf, atomPosition, MP4A)  # mp4a
                remaining -= t._write(t.buf, outStream)
                _copy(inStream, remaining, outStream)
            elif atomType in (MOOV,
                              TRAK,
                              MDIA,
                              MINF,
                              STBL,
                              UDTA):
                t._write(t.buf, outStream)
                walk_atoms(atomEnd)
            else:
                remaining -= t._write(t.buf, outStream)
                _copy(inStream, remaining, outStream)

    walk_atoms(path.getsize(inStream.name))


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
    _bytes = activation_bytes
    im_key = _sha(FIXEDKEY, bytes.fromhex(_bytes))
    iv = _sha(FIXEDKEY, im_key, bytes.fromhex(_bytes))[:16]
    key = im_key[:16]
    # decrypt drm blob to prove we can do it
    cipher = newAES(key, MODE_CBC, iv=iv)
    data = cipher.decrypt(_getAdrmBlob(inStream))
    # check to make sure we haven't misciphered anything up till now
    validDrmChecksum = _sha(key, iv) == _getChecksum(inStream)
    activation_bytes_match = _swapEndian(_bts(data[:4])) == _bytes
    if not validDrmChecksum or not activation_bytes_match:
        raise CredentialMismatch('Either the activation bytes are incorrect'
                                 ' or the audio file is invalid or corrupt.')
    fileKey = _key_mask(data)
    fileDrm = _drm_mask(data)
    inVect = _sha(fileDrm, fileKey, FIXEDKEY, length=16)
    return _bts(fileKey), _bts(inVect)


def _key_mask(data: bytes):
    return data[8:24]


def _drm_mask(data: bytes):
    return data[26:42]


def _getAdrmBlob(inStream: BufferedReader):
    inStream.seek(ADRM_START)
    return _pad_16(inStream.read(ADRM_LENGTH))


def _getChecksum(inStream: BufferedReader):
    inStream.seek(CKSM_START)
    return inStream.read(20)


def _swapEndian(string: str):
    """turns 12345678 into 78563412
    """
    return "".join(map(str.__add__, string[-2::-2], string[-1::-2]))


def _bts(bytes: bytes) -> str:
    return str(hexlify(bytes)).strip("'")[2:]


def _sha(*bits: bytes, length: int = None):
    return sha1(b''.join(bits)).digest()[:length]


def _pad_16(data: bytes) -> bytes:
    length = 16
    length = length - (len(data) % length)
    return data + bytes([length])*length


def _copy(inStream: BufferedReader, length: int, *outs) -> int:
    remaining = length
    while remaining > 0:
        remaining -= \
            __write(inStream.read(min(remaining, 4096)), *outs)
    return length


def __write(buf, *outs: list[BufferedWriter]) -> int:
    for out in outs:
        out.write(buf)
    return len(buf)
