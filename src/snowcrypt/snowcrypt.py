# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
import os
from struct import unpack_from, pack_into
from hashlib import sha1
from io import BufferedReader, BufferedWriter
from math import isclose
from binascii import hexlify
from typing import Tuple

from Crypto.Cipher.AES import MODE_CBC, new as newAES

from .localExceptions import CredentialMismatch, DecryptionFailure
from .constants import *


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

# Atom handlers called programatically.
# Add a new one with the format "_<name>_atom_handler"
# and accept the same arguments as the other handlers


def _meta_atom_handler(inStream, outStream, length, t, **_):
    t.readOne(fint, inStream)
    t.write(outStream)
    _atomizer(inStream, outStream, length)


def _stsd_atom_handler(inStream, outStream, length, t, **_):
    t.readOne(flong, inStream)
    t.write(outStream)
    _atomizer(inStream, outStream, length)


def _aavd_atom_handler(inStream, outStream, length, t, atomPosition=None, **_):
    # change container name so MP4 readers don't complain
    pack_into(fint[0], t.buf, atomPosition, MP4A)
    length -= t.write(outStream)
    outStream.write(inStream.read(length))


def _default_atom_handler(inStream, outStream, length, t, **_):
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


def _mdat_atom_handler(
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
    the rest of the atom is an encrypted AAC audio sample with the above values
    MDAT atoms may contain any number of AAVD atoms, each with the above description
    """
    # this is the main work horse
    t.write(outStream)
    while inStream.tell() < atomEnd:
        t = Translator()
        atom_length = t.readAtomSize(inStream)
        atomTypePosition = t.pos
        atom_type = t.readOne(fint, inStream)

        # after the atom type comes 5 additional fields describing the data.
        # We only care about the last two.
        # skip (in order) time (in ms), first block index,
        # trak number, overall block size, block count
        t.readOne(fint, inStream)
        t.readOne(fint, inStream)
        t.readOne(fint, inStream)
        sum_block_length = t.readOne(fint, inStream)
        block_count = t.readOne(fint, inStream)

        # next come the atom specific fields
        # aavd has a list of sample sizes and then the samples.
        if atom_type in [AAVD, MP4A]:
            # change t.buf's atom_type from AAVD to MP4A or vice versa
            substitute_type = MP4A if atom_type == AAVD else AAVD
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

# End of handlers


_atomFuncs = {
    FTYP: _ftyp_writer,
    MDAT: _mdat_atom_handler,
    AAVD: _aavd_atom_handler,
    META: _meta_atom_handler,
    STSD: _stsd_atom_handler,
    MOOV: _default_atom_handler,
    TRAK: _default_atom_handler,
    MDIA: _default_atom_handler,
    MINF: _default_atom_handler,
    STBL: _default_atom_handler,
    UDTA: _default_atom_handler,
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

        func = _atomFuncs.get(atomType, _just_copy_it)
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

    cipher = newAES(key, MODE_CBC, iv=iv)
    inStream.seek(ADRM_START)
    data = _pad_16(inStream.read(ADRM_LENGTH))
    data = cipher.decrypt(data)

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


def key_and_iv_for_file_with_abytes(file: str, activation_bytes: str) -> Tuple:
    """convenience function for key derivation"""
    with open(file, 'rb') as f:
        return deriveKeyIV(f, activation_bytes)


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
