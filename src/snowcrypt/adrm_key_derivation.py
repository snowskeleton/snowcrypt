from hashlib import sha1
from io import BufferedReader
from binascii import hexlify
from typing import Tuple

from Crypto.Cipher.AES import MODE_CBC, new as newAES

from .localExceptions import CredentialMismatch
from .constants import *  # noqa


def deriveKeyIV(inStream: BufferedReader, activation_bytes: str):
    """derive key and initialization vector for given BufferReader

    Args:
        inStream (BufferedReader): open file stream
        activation_bytes (str): decryption bytes unique to your account

    Returns:
        tuple[str, str]: key, initialization vector
    """
    file_start = inStream.tell()
    im_key = _sha(FIXEDKEY, bytes.fromhex(activation_bytes))  # noqa
    iv = _sha(FIXEDKEY, im_key, bytes.fromhex(activation_bytes), length=16)  # noqa
    key = im_key[:16]

    cipher = newAES(key, MODE_CBC, iv=iv)
    inStream.seek(ADRM_START)  # noqa
    data = _pad_16(inStream.read(ADRM_LENGTH))  # noqa
    data = cipher.decrypt(data)

    inStream.seek(CKSM_START)  # noqa
    real_checksum = inStream.read(CKSM_LENGTH)  # noqa
    derived_checksum = _sha(key, iv)
    validDrmChecksum = derived_checksum == real_checksum

    real_bites = _swapEndian(_bts(data[:4]))
    activation_bytes_match = real_bites == activation_bytes
    if not validDrmChecksum or not activation_bytes_match:
        raise CredentialMismatch('Either the activation bytes are incorrect'
                                 ' or the audio file is invalid or corrupt.')

    fileKey = _key_mask(data)
    fileDrm = _drm_mask(data)
    inVect = _sha(fileDrm, fileKey, FIXEDKEY, length=16)  # noqa
    inStream.seek(file_start)

    return _bts(fileKey), _bts(inVect)


def key_and_iv_for_file_with_abytes(file: str, activation_bytes: str) -> Tuple:
    """convenience function for key derivation"""
    with open(file, 'rb') as f:
        return deriveKeyIV(f, activation_bytes)


def _bts(bytes: bytes) -> str: return str(hexlify(bytes)).strip("'")[2:]


def _key_mask(data: bytes): return data[8:24]


def _drm_mask(data: bytes): return data[26:42]


def _swapEndian(string: str):
    """turns 12345678 into 78563412
    """
    return "".join(map(str.__add__, string[-2::-2], string[-1::-2]))


def _sha(*bits: bytes, length: int = None):
    return sha1(b''.join(bits)).digest()[:length]


def _pad_16(data: bytes, length: int = 16) -> bytes:
    length = length - (len(data) % length)
    return data + bytes([length])*length
