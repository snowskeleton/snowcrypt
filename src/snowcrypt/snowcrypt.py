# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
from struct import unpack_from, pack_into
from os import path
from hashlib import sha1
from io import BufferedReader, BufferedWriter

from Crypto.Cipher import AES
from binascii import hexlify

from .localExceptions import CredentialMismatch
from .atomTypes import *


fshort, fint, flong = (">h", 2), (">i", 4), (">q", 8)


class Translator:
    def __init__(self, size=None):
        self.buf = bytearray(size if size != None else 4096)
        self.pos, self.wpos = 0, 0

    def reset(self):
        self.pos, self.wpos = 0, 0

    def _position(self) -> int: return self.pos
    def _getShort(self) -> int: return self._getOne(fshort)
    def _getInt(self) -> int: return self._getOne(fint)
    def _getLong(self) -> int: return self._getOne(flong)

    def _putInt(self, position: int, value: int): self._putOne(
        fint, position, value)

    def _getOne(self, format):
        r = unpack_from(format[0], self.buf, self.pos)[0]
        self.pos = self.pos + format[1]
        return r

    def _putOne(self, format: str | bytes, position: int, value):
        pack_into(format[0], self.buf, position, value)

    def _readOne(self, inStream: BufferedReader, format: str | bytes):
        length = format[1]
        self.buf[self.wpos: self.wpos + length] = inStream.read(length)
        r = unpack_from(format[0], self.buf, self.pos)[0]
        self.wpos = self.wpos + length
        self.pos = self.pos + length
        return r

    def _readInto(self, inStream: BufferedReader, length: int | None) -> int:
        self.buf[self.wpos: self.wpos + length] = inStream.read(length)
        self.wpos = self.wpos + length
        return length

    def _write(self, *outs) -> int:
        if self.wpos > 0:
            # fuck you python and your write function that can't sublist!
            data = self.buf if self.wpos == len(
                self.buf) else self.buf[0: self.wpos]
            for out in outs:
                out.write(data)
            return self.wpos
        return 0

    def _readInt(self, inStream: BufferedReader) -> int:
        return self._readOne(inStream, fint)

    def _readLong(self, inStream: BufferedReader) -> int:
        return self._readOne(inStream, flong)

    def _skipLong(self): self._skip(flong[1])
    def _skip(self, length): self.pos = self.pos + length

    def _readAtomSize(self, inStream: BufferedReader) -> int:
        atomLength = self._readInt(inStream)
        return atomLength if atomLength != 1 else self._readLong(inStream)

    def _zero(self, start=0, end=None):
        if end == None:
            end = self.wpos
        for i in range(start, end):
            self.buf[i] = 0

    def _fillFtyp(self, inStream, remaining, outStream):
        length = self._readInto(inStream, remaining)
        self._putInt(0,  M4A)
        self._putInt(4,  VERSION2_0)
        self._putInt(8,  ISO2)
        self._putInt(12, M4B)
        self._putInt(16, MP42)
        self._putInt(20, ISOM)
        self._zero(24, length)
        self._write(outStream)


def _decrypt(inStream: BufferedReader, outStream: BufferedWriter, key: bytes, iv: bytes):
    def walk_mdat(endPosition: int):  # samples
        while inStream.tell() < endPosition:
            t = Translator()
            atomLength = t._readAtomSize(inStream)
            atomTypePosition = t._position()
            atomType = t._readInt(inStream)

            # after the atom type comes 5 additional fields describing the data.
            # We only care about the last two.
            t._readInto(inStream, 20)
            t.pos += 12  # skip time in ms, first block index, trak number
            totalBlockSize = t._getInt()  # total size of all blocks
            blockCount = t._getInt()  # number of blocks

            # next come the atom specific fields
            # aavd has a list of sample sizes and then the samples.
            if atomType == AAVD:
                # replace aavd type with mp4a type
                t._putInt(atomTypePosition, MP4A)
                t._readInto(inStream, blockCount * 4)
                t._write(outStream)

                for _ in range(blockCount):
                    # setup
                    sampleLength = t._getInt()
                    aes = AES.new(key, AES.MODE_CBC, iv=iv)

                    # for cipher padding, (up to) last 2 bytes are unencrypted
                    encryptedLength = sampleLength & 0xFFFFFFF0
                    unencryptedLength = sampleLength & 0x0000000F

                    encryptedData = inStream.read(encryptedLength)
                    unencryptedData = inStream.read(unencryptedLength)

                    outStream.write(aes.decrypt(encryptedData))
                    outStream.write(unencryptedData)

            else:
                length = t._write(outStream)
                _copy(inStream, atomLength +
                      totalBlockSize - length, outStream)

    def walk_atoms(endPosition: int):  # everything
        while inStream.tell() < endPosition:
            t = Translator()
            atomStart = inStream.tell()
            atomLength = t._readAtomSize(inStream)
            atomEnd = atomStart + atomLength
            atomPosition = t._position()
            atomType = t._readInt(inStream)

            remaining = atomLength

            if atomType == FTYP:
                remaining -= t._write(outStream)
                t.reset()
                t._fillFtyp(inStream, remaining, outStream)
            elif atomType == META:
                t._readInto(inStream, 4)
                t._write(outStream)
                walk_atoms(atomEnd)
            elif atomType == STSD:
                t._readInto(inStream, 8)
                t._write(outStream)
                walk_atoms(atomEnd)
            elif atomType == MDAT:
                t._write(outStream)
                walk_mdat(atomEnd)
            elif atomType == AAVD:
                t._putInt(atomPosition, 0x6d703461)  # mp4a
                remaining -= t._write(outStream)
                _copy(inStream, remaining, outStream)
            elif atomType == MOOV \
                    or atomType == TRAK \
                    or atomType == MDIA \
                    or atomType == MINF \
                    or atomType == STBL \
                    or atomType == UDTA:
                t._write(outStream)
                walk_atoms(atomEnd)
            else:
                remaining -= t._write(outStream)
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
    fixedKey = bytes.fromhex('77214d4b196a87cd520045fd20a51d67')
    _bytes = activation_bytes
    im_key = _snowsha(fixedKey, bytes.fromhex(_bytes))
    iv = _snowsha(fixedKey, im_key, bytes.fromhex(_bytes))[:16]
    key = im_key[:16]
    # decrypt drm blob to prove we can do it
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    data = cipher.decrypt(_pad(_getAdrmBlob(inStream), 16))
    try:
        assert _snowsha(key, iv) == _getChecksum(inStream)
        assert _swapEndien(_bts(data[:4])) == _bytes
    except AssertionError:
        raise CredentialMismatch('Either the activation bytes are incorrect'
                                 ' or the audio file is invalid or corrupt.')
    # if we didn't raise any exceptions, then this file can
    # be decrypted with the provided activation_bytes
    fileKey = _getKey(data)
    fileDrm = _getDrm(data)
    inVect = _snowsha(fileDrm, fileKey, fixedKey)[:16]
    return _bts(fileKey), _bts(inVect)


def _getKey(data: bytes):
    """
    Args:
        data (bytes): decrypted adrmBlob

    Returns:
        bytes: final AES decryption key
    """
    return data[8:24]


def _getDrm(data: bytes):
    """
    Args:
        data (bytes): decrypted adrmBlob

    Returns:
        bytes: sha key derivation piece from drm blob
    """
    return data[26:42]


def _getAdrmBlob(inStream: BufferedReader):
    """read ADRM from inStream

    Args:
        inStream (BufferReader): an open file stream

    Returns:
        int: adrm blob
    """
    inStream.seek(0x251)
    return inStream.read(56)


def _getChecksum(inStream: BufferedReader):
    """read file checksum from inStream

    Args:
        inStream (BufferReader): an open file stream

    Returns:
        int: checksum
    """
    inStream.seek(0x28d)
    return inStream.read(20)


def _swapEndien(string: str):
    """return bytes-like string with swapped endian
    turns 12345678 into 78563412

    Args:
        string (str): hex string

    Returns:
        str: reversed string
    """
    return "".join(map(str.__add__, string[-2::-2], string[-1::-2]))


def _bts(bytes: bytes) -> str:
    """convenience function for cleaning up values

    Args:
        bytes (bytes): bytes-like object we want as string

    Returns:
        str: stringy bytes
    """
    # turns "b'bytes'"" into "hexstring"
    return str(hexlify(bytes)).strip("'")[2:]


def _snowsha(*bits: bytes, length: int = None):
    """convenience function for deriving keys

    Args:
        bits (bytes): input data for sha hash
        length (int, optional): return only first length characters. Defaults to None (which is All)

    Returns:
        bytes: sha digest
    """
    return sha1(b''.join(bits)).digest()[:length]


def _pad(data: bytes, length: int = 16) -> bytes:
    """pad data to nearest length multiple

    Args:
        data (bytes): byte data
        length (int, optional): Length to pad to. Defaults to 16

    Returns:
        bytes: same bytes appended with N additional bytes of value N,
        where N is len(data) modulus length
    """
    length = length - (len(data) % length)
    return data + bytes([length])*length


def _copy(inStream: BufferedReader, length: int, *outs) -> int:
    remaining = length
    while remaining > 0:
        remaining -= \
            __write(inStream.read(min(remaining, 4096)), *outs)
    return length


def __write(buf, *outs) -> int:
    for out in outs:
        out.write(buf)
    return len(buf)
