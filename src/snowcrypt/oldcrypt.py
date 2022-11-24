# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
import struct
import os
import hashlib
import io

from Crypto.Cipher import AES
from binascii import hexlify

from .localExceptions import CredentialMismatch


class Translator:
    fshort, fint, flong = (">h", 2), (">i", 4), (">q", 8)

    def __init__(self, size=None):
        self.buf = bytearray(size if size != None else 4096)
        self.pos, self.wpos = 0, 0

    def reset(self):
        self.pos, self.wpos = 0, 0

    def position(self) -> int: return self.pos
    def getShort(self) -> int: return self.getOne(self.fshort)
    def getInt(self) -> int: return self.getOne(self.fint)
    def getLong(self) -> int: return self.getOne(self.flong)

    def putInt(self, position: int, value: int): self.putOne(
        self.fint, position, value)

    def getOne(self, format):
        r = struct.unpack_from(format[0], self.buf, self.pos)[0]
        self.pos = self.pos + format[1]
        return r

    def putOne(self, format: str | bytes, position: int, value):
        struct.pack_into(format[0], self.buf, position, value)

    def readOne(self, inStream: io.BufferedReader, format: str | bytes):
        length = format[1]
        self.buf[self.wpos: self.wpos + length] = inStream.read(length)
        r = struct.unpack_from(format[0], self.buf, self.pos)[0]
        self.wpos = self.wpos + length
        self.pos = self.pos + length
        return r

    def readInto(self, inStream: io.BufferedReader, length: int | None) -> int:
        self.buf[self.wpos: self.wpos + length] = inStream.read(length)
        self.wpos = self.wpos + length
        return length

    def readCount(self) -> int: return self.wpos

    def write(self, *outs) -> int:
        if self.wpos > 0:
            # fuck you python and your write function that can't sublist!
            data = self.buf if self.wpos == len(
                self.buf) else self.buf[0: self.wpos]
            for out in outs:
                out.write(data)
            return self.wpos
        return 0

    def readInt(self, inStream: io.BufferedReader) -> int:
        return self.readOne(inStream, self.fint)

    def readLong(self, inStream: io.BufferedReader) -> int:
        return self.readOne(inStream, self.flong)

    def skipInt(self): self.skip(self.fint[1])
    def skipLong(self): self.skip(self.flong[1])
    def skip(self, length): self.pos = self.pos + length

    def readAtomSize(self, inStream: io.BufferedReader) -> int:
        atomLength = self.readInt(inStream)
        return atomLength if atomLength != 1 else self.readLong(inStream)

    def zero(self, start=0, end=None):
        if end == None:
            end = self.wpos
        for i in range(start, end):
            self.buf[i] = 0

    def write_and_reset(self, *outs) -> int:
        r = self.write(*outs)
        self.reset()
        return r


class AaxDecrypter:
    def __init__(self, inStream: io.BufferedReader, outStream: io.BufferedWriter, key: str, iv: str):
        self.key = bytes.fromhex(key)
        self.iv = bytes.fromhex(iv)
        self.inStream = inStream
        self.outStream = outStream

    def walk_mdat(self, translator: Translator, endPosition: int):  # samples
        inStream = self.inStream
        outStream = self.outStream
        startPosition = inStream.tell()
        # It's illegal for mdat to contain atoms... but that didn't stop Audible! Not that any parsers care.
        while inStream.tell() < endPosition:
            # read an atom length.
            atomStart = inStream.tell()
            translator.reset()
            atomLength = translator.readAtomSize(inStream)
            atomTypePosition = translator.position()
            atomType = translator.readInt(inStream)

            # after the atom type comes 5 additional fields describing the data.
            # We only care about the last two.
            translator.readInto(inStream, 20)
            translator.skipInt()  # time in ms
            translator.skipInt()  # first block index
            translator.skipInt()  # trak number
            totalBlockSize = translator.getInt()  # total size of all blocks
            blockCount = translator.getInt()  # number of blocks

            # atomEnd = atomStart + atomLength + totalBlockSize

            # next come the atom specific fields
            # aavd has a list of sample sizes and then the samples.
            if (atomType == 0x61617664):  # aavd
                translator.putInt(atomTypePosition, 0x6d703461)  # mp4a
                translator.readInto(inStream, blockCount * 4)
                translator.write(outStream)
                for _ in range(blockCount):
                    sampleLength = translator.getInt()
                    # has to be reset every go round.
                    cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
                    remaining = sampleLength - \
                        outStream.write(cipher.decrypt(
                            inStream.read(sampleLength & 0xFFFFFFF0)))
                    # fun fact, the last few bytes of each sample aren't encrypted!
                    if remaining > 0:
                        self.copy(inStream, remaining, outStream)
            else:
                len = translator.write_and_reset(outStream)
                self.copy(inStream, atomLength +
                          totalBlockSize - len, outStream)
            translator.reset()

        return endPosition - startPosition

    def walk_atoms(self, translator: Translator, endPosition: int):  # everything
        inStream = self.inStream
        outStream = self.outStream
        startPosition = inStream.tell()
        while inStream.tell() < endPosition:
            # read an atom length.
            translator.reset()
            atomStart = inStream.tell()
            atomLength = translator.readAtomSize(inStream)
            atomEnd = atomStart + atomLength
            ap = translator.position()
            atom = translator.readInt(inStream)

            remaining = atomLength

            if atom == 0x66747970:  # ftyp-none
                remaining = remaining - translator.write_and_reset(outStream)
                len = translator.readInto(inStream, remaining)
                translator.putInt(0,  0x4D344120)  # "M4A "
                translator.putInt(4,  0x00000200)  # version 2.0?
                translator.putInt(8,  0x69736F32)  # "iso2"
                translator.putInt(12, 0x4D344220)  # "M4B "
                translator.putInt(16, 0x6D703432)  # "mp42"
                translator.putInt(20, 0x69736F6D)  # "isom"
                translator.zero(24, len)
                remaining = remaining - \
                    translator.write_and_reset(outStream)
            elif atom == 0x6d6f6f76 \
                    or atom == 0x7472616b \
                    or atom == 0x6d646961 \
                    or atom == 0x6d696e66 \
                    or atom == 0x7374626c \
                    or atom == 0x75647461:  # moov-0, trak-0, mdia-0, minf-0, stbl-0, udta-0
                remaining = remaining - translator.write_and_reset(outStream)
                remaining = remaining - \
                    self.walk_atoms(translator, atomEnd)
            elif atom == 0x6D657461:  # meta-4
                translator.readInto(inStream, 4)
                remaining = remaining - \
                    translator.write_and_reset(outStream)
                remaining = remaining - \
                    self.walk_atoms(translator, atomEnd)
            elif atom == 0x73747364:  # stsd-8
                translator.readInto(inStream, 8)
                remaining = remaining - \
                    translator.write_and_reset(outStream)
                remaining = remaining - \
                    self.walk_atoms(translator, atomEnd)
            elif atom == 0x6d646174:  # mdat-none
                remaining = remaining - translator.write_and_reset(outStream)
                remaining = remaining - \
                    self.walk_mdat(translator, atomEnd)
            elif atom == 0x61617664:  # aavd-variable
                translator.putInt(ap, 0x6d703461)  # mp4a
                remaining = remaining - \
                    translator.write_and_reset(outStream)
                # don't care about the children.
                self.copy(inStream, remaining, outStream)
            else:
                remaining = remaining - translator.write_and_reset(outStream)
                # don't care about the children.
                self.copy(inStream, remaining, outStream)

        return endPosition - startPosition

    def status(self, position, filesize):
        None

    def copy(self, inStream, length, *outs) -> int:
        remaining = length
        while remaining > 0:
            remaining = remaining - \
                self.write(inStream.read(min(remaining, 4096)), *outs)
        return length

    def write(self, buf, *outs) -> int:
        for out in outs:
            out.write(buf)
        return len(buf)


def decrypt_aaxc(inpath: str, outpath: str, key: int, iv: int):
    """converts inpath with key and iv, writing to outpath

    Args:
        inpath (str): source
        outpath (str): destination
        key (int): AES key
        iv (int): AES initialization vector
    """
    with open(inpath, 'rb') as src:
        with open(outpath, 'wb') as dest:
            decrypter = AaxDecrypter(src, dest, key, iv)
            decrypter.walk_atoms(Translator(), os.path.getsize(inpath))


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


def deriveKeyIV(inStream: io.BufferedReader, activation_bytes: str):
    """derive key and initialization vector for given io.BufferReader

    Args:
        inStream (io.BufferedReader): open file stream
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


def _getAdrmBlob(inStream: io.BufferedReader):
    """read ADRM from inStream

    Args:
        inStream (io.BufferReader): an open file stream

    Returns:
        int: adrm blob
    """
    inStream.seek(0x251)
    return inStream.read(56)


def _getChecksum(inStream: io.BufferedReader):
    """read file checksum from inStream

    Args:
        inStream (io.BufferReader): an open file stream

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
    return hashlib.sha1(b''.join(bits)).digest()[:length]


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
