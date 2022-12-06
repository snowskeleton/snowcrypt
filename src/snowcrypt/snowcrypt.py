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
        pack_into(fint[0], buf, 0,  TYPES.M4A)
        pack_into(fint[0], buf, 4,  TYPES.VERSION2_0)
        pack_into(fint[0], buf, 8,  TYPES.ISO2)
        pack_into(fint[0], buf, 12, TYPES.M4B)
        pack_into(fint[0], buf, 16, TYPES.MP42)
        pack_into(fint[0], buf, 20, TYPES.ISOM)
        # pack_into(format[0], buffer, position, value)
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
            if atomType == TYPES.AAVD:
                # replace aavd type with mp4a type
                pack_into(fint[0], t.buf,  atomTypePosition, TYPES.MP4A)
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

            if atomType == TYPES.FTYP:
                remaining -= t._write(t.buf, outStream)
                t.pos, t.wpos = 0, 0
                t._fillFtyp(inStream, remaining, outStream)
            elif atomType == TYPES.META:
                t._readInto(inStream, 4)
                t._write(t.buf, outStream)
                walk_atoms(atomEnd)
            elif atomType == TYPES.STSD:
                t._readInto(inStream, 8)
                t._write(t.buf, outStream)
                walk_atoms(atomEnd)
            elif atomType == TYPES.MDAT:
                t._write(t.buf, outStream)
                walk_mdat(atomEnd)
            elif atomType == TYPES.AAVD:
                pack_into(fint[0], t.buf, atomPosition, TYPES.MP4A)  # mp4a
                remaining -= t._write(t.buf, outStream)
                _copy(inStream, remaining, outStream)
            elif atomType in (TYPES.MOOV,
                              TYPES.TRAK,
                              TYPES.MDIA,
                              TYPES.MINF,
                              TYPES.STBL,
                              TYPES.UDTA):
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
