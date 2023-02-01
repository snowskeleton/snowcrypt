# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
import os
from io import BufferedReader, BufferedWriter
from math import isclose
from struct import unpack_from, pack_into

from Crypto.Cipher.AES import MODE_CBC, new as newAES

from .adrm_key_derivation import key_and_iv_for_file_with_abytes
from .constants import *  # noqa
from .localExceptions import DecryptionFailure


fshort, fint, flong = (">h", 2), (">i", 4), (">q", 8)


class Translator:
    def __init__(self, size: int = None):
        self.buf = bytearray(size if size is not None else 4096)
        self.pos, self.wpos = 0, 0

    def _readInto(self, inStream: BufferedReader, length: int or None) -> int:
        start = self.wpos
        self.buf[start:start + length] = inStream.read(length)
        self.wpos += length
        return length

    def next(self, format: tuple):
        data = unpack_from(format[0], self.buf, self.pos)[0]
        self.pos += format[1]
        return data

    def readAtomSize(self, inStream: BufferedReader) -> int:
        atomLength = self.readOne(fint, inStream)
        return atomLength if atomLength != 1 else self.readOne(flong, inStream)

    def readOne(self, format: tuple, inStream: BufferedReader):
        length = format[1]
        self._readInto(inStream, length)
        r = self.next(format)
        return r

    def write(self, out: BufferedWriter) -> int:
        end = self.wpos
        data = self.buf[0:end]
        out.write(data)
        return self.wpos


def _decrypt_aavd(inStream: BufferedReader, key, iv, t: Translator):
    # setup
    length = t.next(fint)
    aes = newAES(key, MODE_CBC, iv=iv)

    # for cipher padding, (up to) last 2 bytes are unencrypted
    encryptedLength = length & 0xFFFFFFF0
    unencryptedLength = length & 0x0000000F

    encryptedData = inStream.read(encryptedLength)
    unencryptedData = inStream.read(unencryptedLength)

    data = aes.decrypt(encryptedData) + unencryptedData
    return data


class Handler:
    def meta(inStream, outStream, length, t, **_):
        t.readOne(fint, inStream)
        t.write(outStream)
        _atomizer(inStream, outStream, length)

    def stsd(inStream, outStream, length, t, **_):
        t.readOne(flong, inStream)
        t.write(outStream)
        _atomizer(inStream, outStream, length)

    def aavd(inStream, outStream, length, t, atomPosition=None, **_):
        # change container name so MP4 readers don't complain
        pack_into(fint[0], t.buf, atomPosition, MP4A)  # noqa
        length -= t.write(outStream)
        outStream.write(inStream.read(length))

    def default(inStream, outStream, length, t, **_):
        t.write(outStream)
        _atomizer(inStream, outStream, length)

    def just_copy_it(inStream, outStream, length, t, **_):
        length -= t.write(outStream)
        outStream.write(inStream.read(length))

    def ftyp_writer(inStream, outStream, length, t, **_):
        length -= t.write(outStream)
        buf = bytearray(length)
        pos = 0
        for tag in FTYP_TAGS:  # noqa
            pack_into(fint[0], buf, pos, tag)
            pos += 4
        for i in range(24, length):
            buf[i] = 0
        outStream.write(buf)
        inStream.read(length)

    def mdat(
            inStream: BufferedReader,
            outStream: BufferedWriter,
            length: int,
            t: Translator,
            encrypt: bool = False,
            atomEnd: int = None,
            key=None,
            iv=None,
            ** _,
    ):
        """
        description of MDAT atom in .aax and .aaxc files
        size.......   type (aavd)   empty......   empty......
        00 00 00 48   61 61 76 64   00 00 00 00   00 00 00 00
        empty......   sum blk len   block count
        00 00 00 00   00 00 01 6c   00 00 01 6c ...
        the rest is any number of AAVD atoms containing encrypted AAC samples
        """
        # this is the main work horse
        t.write(outStream)
        while inStream.tell() < atomEnd:
            t = Translator()
            atom_length = t.readAtomSize(inStream)
            atomTypePosition = t.pos
            atom_type = t.readOne(fint, inStream)

            # after atom type, 5 additional fields describing the data.
            # We only care about the last two.
            # skip (in order) time in ms, first block index,
            # trak number, overall block size, block count
            t.readOne(fint, inStream)
            t.readOne(fint, inStream)
            t.readOne(fint, inStream)
            sum_block_length = t.readOne(fint, inStream)
            block_count = t.readOne(fint, inStream)

            # next come the atom specific fields
            # aavd has a list of sample sizes and then the samples.
            if atom_type in [AAVD, MP4A]:  # noqa
                # change t.buf's atom_type from AAVD to MP4A or vice versa
                substitute_type = MP4A if atom_type == AAVD else AAVD  # noqa
                pack_into(fint[0], t.buf,  atomTypePosition, substitute_type)

                # sample sizes
                t._readInto(inStream, block_count * 4)

                # flush buffer
                t.write(outStream)

                for _ in range(block_count):
                    decrypted_block = _decrypt_aavd(inStream, key, iv, t)
                    outStream.write(decrypted_block)

            else:  # TEXT atom
                offset = t.write(outStream)
                outStream.write(inStream.read(
                    atom_length + sum_block_length - offset))


_atomFuncs = {
    FTYP: Handler.ftyp_writer,  # noqa
    MDAT: Handler.mdat,  # noqa
    AAVD: Handler.aavd,  # noqa
    META: Handler.meta,  # noqa
    STSD: Handler.stsd,  # noqa
    MOOV: Handler.default,  # noqa
    TRAK: Handler.default,  # noqa
    MDIA: Handler.default,  # noqa
    MINF: Handler.default,  # noqa
    STBL: Handler.default,  # noqa
    UDTA: Handler.default,  # noqa
}


def _atomizer(
    inStream: BufferedReader = None,
    outStream: BufferedWriter = None,
    eof: int = None,
    key=None,
    iv=None,
    encrypt: bool = False,
):
    eof = eof if eof is not None else os.path.getsize(inStream.name)
    while inStream.tell() < eof:
        t = Translator()
        atomStart = inStream.tell()
        length = t.readAtomSize(inStream)
        atomPosition = t.pos
        atomType = t.readOne(fint, inStream)

        func = _atomFuncs.get(atomType, Handler.just_copy_it)
        func(
            atomEnd=atomStart + length,
            atomPosition=atomPosition,
            outStream=outStream,
            inStream=inStream,
            encrypt=encrypt,
            length=length,
            key=key,
            iv=iv,
            t=t,
        )


def decrypt_aaxc(inpath: str, outpath: str, key: int, iv: int):
    """converts inpath with key and iv, writing to outpath

    Args:
        inpath (str): source
        outpath (str): destination
        key (int): AES key
        iv (int): AES initialization vector
    """
    if not os.path.exists(inpath):
        raise FileNotFoundError(inpath)

    key = bytes.fromhex(key)
    iv = bytes.fromhex(iv)
    with open(inpath, 'rb') as src:
        with open(outpath, 'wb') as dest:
            _atomizer(
                outStream=dest,
                inStream=src,
                key=key,
                iv=iv,
            )
            s1 = os.path.getsize(src.name)
            s2 = os.path.getsize(dest.name)
            if not isclose(s1, s2, rel_tol=0.10):
                msg = f'"{dest.name}" size of {s2} '
                msg += f'does not match "{src.name}" size of {s1}'
                raise DecryptionFailure(msg)


def decrypt_aax(inpath: str, outpath: str, activation_bytes: str):
    """convenience function for deriving AES key and initialization vector,
    then decrypting with those values.

    Args:
        inpath (str): file path to input
        outpath (str): file path to output
        activation_bytes (str): decryption bytes unique to your account
    """
    if not os.path.exists(inpath):
        raise FileNotFoundError(inpath)

    key, iv = key_and_iv_for_file_with_abytes(inpath, activation_bytes)
    decrypt_aaxc(inpath, outpath, key, iv)
