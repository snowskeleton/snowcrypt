# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
from struct import unpack_from, pack_into
from os import path
from hashlib import sha1
from io import BufferedReader, BufferedWriter

from Crypto.Cipher.AES import MODE_CBC, new as newAES
from binascii import hexlify

from .localExceptions import CredentialMismatch
from .atomTypes import TYPES


fshort, fint, flong = (">h", 2), (">i", 4), (">q", 8)


class Translator:
    def __init__(self, size: int = None):
        self.buf = bytearray(size if size != None else 4096)
        self.pos, self.wpos = 0, 0

    def _getOne(self, format: tuple):
        r = unpack_from(format[0], self.buf, self.pos)[0]
        self.pos = self.pos + format[1]
        return r

    def _putOne(self, format: str or bytes, position: int, value):
        pack_into(format[0], self.buf, position, value)

    def _readOne(self, format: str or bytes, inStream: BufferedReader):
        length = format[1]
        self._readInto(inStream, length, reset=False)
        r = unpack_from(format[0], self.buf, self.pos)[0]
        self.wpos = self.wpos + length
        self.pos = self.pos + length
        return r

    def _readInto(self, inStream: BufferedReader, length: int | None, reset: bool = True) -> int:
        self.buf[self.wpos: self.wpos + length] = inStream.read(length)
        if reset:
            self.wpos = self.wpos + length
        return length

    def _write(self, *outs: list[BufferedWriter]) -> int:
        if self.wpos > 0:
            # fuck you python and your write function that can't sublist!
            data = self.buf if self.wpos == len(
                self.buf) else self.buf[0: self.wpos]
            for out in outs:
                out.write(data)
            return self.wpos
        return 0

    def _readAtomSize(self, inStream: BufferedReader) -> int:
        atomLength = self._readOne(fint, inStream)
        return atomLength if atomLength != 1 else self._readOne(flong, inStream)

    def _zero(self, start: int = 0, end: int = None):
        for i in range(start, end if end else self.wpos):
            self.buf[i] = 0

    def _fillFtyp(self, inStream: BufferedReader, remaining: int, outStream: BufferedWriter):
        length = self._readInto(inStream, remaining)
        self._putOne(fint, 0,  TYPES.M4A)
        self._putOne(fint, 4,  TYPES.VERSION2_0)
        self._putOne(fint, 8,  TYPES.ISO2)
        self._putOne(fint, 12, TYPES.M4B)
        self._putOne(fint, 16, TYPES.MP42)
        self._putOne(fint, 20, TYPES.ISOM)
        self._zero(24, length)
        self._write(outStream)


def _decrypt(inStream: BufferedReader, outStream: BufferedWriter, key: bytes, iv: bytes):
    def walk_mdat(endPosition: int):  # samples
        while inStream.tell() < endPosition:
            t = Translator()
            atomLength = t._readAtomSize(inStream)
            atomTypePosition = t.pos
            atomType = t._readOne(fint, inStream)

            # after the atom type comes 5 additional fields describing the data.
            # We only care about the last two.
            t._readInto(inStream, 20)
            t.pos += 12  # skip time in ms, first block index, trak number
            totalBlockSize = t._getOne(fint)  # total size of all blocks
            blockCount = t._getOne(fint)  # number of blocks

            # next come the atom specific fields
            # aavd has a list of sample sizes and then the samples.
            if atomType == TYPES.AAVD:
                # replace aavd type with mp4a type
                t._putOne(fint, atomTypePosition, TYPES.MP4A)
                t._readInto(inStream, blockCount * 4)
                t._write(outStream)

                for _ in range(blockCount):
                    # setup
                    sampleLength = t._getOne(fint)
                    aes = newAES(key, MODE_CBC, iv=iv)

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
            atomPosition = t.pos
            atomType = t._readOne(fint, inStream)

            remaining = atomLength

            if atomType == TYPES.FTYP:
                remaining -= t._write(outStream)
                t.pos, t.wpos = 0, 0
                t._fillFtyp(inStream, remaining, outStream)
            elif atomType == TYPES.META:
                t._readInto(inStream, 4)
                t._write(outStream)
                walk_atoms(atomEnd)
            elif atomType == TYPES.STSD:
                t._readInto(inStream, 8)
                t._write(outStream)
                walk_atoms(atomEnd)
            elif atomType == TYPES.MDAT:
                t._write(outStream)
                walk_mdat(atomEnd)
            elif atomType == TYPES.AAVD:
                t._putOne(fint, atomPosition, TYPES.MP4A)  # mp4a
                remaining -= t._write(outStream)
                _copy(inStream, remaining, outStream)
            elif atomType == TYPES.MOOV \
                    or atomType == TYPES.TRAK \
                    or atomType == TYPES.MDIA \
                    or atomType == TYPES.MINF \
                    or atomType == TYPES.STBL \
                    or atomType == TYPES.UDTA:
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
    iv = _snowsha(fixedKey, im_key, bytes.fromhex(_bytes))  # [:16]
    key = im_key[:16]
    # decrypt drm blob to prove we can do it
    cipher = newAES(key, MODE_CBC, iv=iv)
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


def __write(buf, *outs: list[BufferedWriter]) -> int:
    for out in outs:
        out.write(buf)
    return len(buf)
