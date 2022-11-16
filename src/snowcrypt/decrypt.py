# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
import struct
from Crypto.Cipher import AES
import os
import sys


class Translator:
    fshort, fint, flong = (">h", 2), (">i", 4), (">q", 8)

    def __init__(self, size=None):
        self.buf = bytearray(size if size != None else 4096)
        self.pos, self.wpos = 0, 0

    def reset(self):
        self.pos, self.wpos = 0, 0

    def position(self): return self.pos
    def getShort(self): return self.getOne(self.fshort)
    def getInt(self): return self.getOne(self.fint)
    def getLong(self): return self.getOne(self.flong)
    def putInt(self, position, value): self.putOne(self.fint, position, value)

    def getOne(self, format):
        r = struct.unpack_from(format[0], self.buf, self.pos)[0]
        self.pos = self.pos + format[1]
        return r

    def putOne(self, format, position, value):
        struct.pack_into(format[0], self.buf, position, value)

    def readOne(self, inStream, format):
        length = format[1]
        self.buf[self.wpos: self.wpos + length] = inStream.read(length)
        r = struct.unpack_from(format[0], self.buf, self.pos)[0]
        self.wpos = self.wpos + length
        self.pos = self.pos + length
        return r

    def readInto(self, inStream, length) -> int:
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

    def readInt(self, inStream):
        return self.readOne(inStream, self.fint)

    def readLong(self, inStream):
        return self.readOne(inStream, self.flong)

    def skipInt(self): self.skip(self.fint[1])
    def skipLong(self): self.skip(self.flong[1])
    def skip(self, length): self.pos = self.pos + length

    def readAtomSize(self, inStream):
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
    filetypes = {6: "html", 7: "xml", 12: "gif",
                 13: "jpg", 14: "png", 15: "url", 27: "bmp"}

    def __init__(self, inStream, outStream, key, iv):
        self.key = bytes.fromhex(key)
        self.iv = bytes.fromhex(iv)
        self.inStream = inStream
        self.outStream = outStream

    def walk_mdat(self, translator, endPosition):  # samples
        inStream = self.inStream
        outStream = self.outStream
        startPosition = inStream.tell()
        # It's illegal for mdat to contain atoms... but that didn't stop Audible! Not that any parsers care.
        while inStream.tell() < endPosition:
            # self.status(inStream.tell(), self.filesize)
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

            atomEnd = atomStart + atomLength + totalBlockSize

            # next come the atom specific fields
            # aavd has a list of sample sizes and then the samples.
            if (atomType == 0x61617664):
                translator.putInt(atomTypePosition, 0x6d703461)  # mp4a
                translator.readInto(inStream, blockCount * 4)
                translator.write(outStream)
                for _ in range(blockCount):
                    # self.status(inStream.tell(),  self.filesize)
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
            self.checkPosition(atomEnd)

        return endPosition - startPosition

    def walk_atoms(self, translator, endPosition):  # everything
        inStream = self.inStream
        outStream = self.outStream
        startPosition = inStream.tell()
        while inStream.tell() < endPosition:
            # self.status(inStream.tell(), self.filesize)
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

            self.checkPosition(atomEnd)

        # self.status(inStream.tell(), self.filesize)
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

    def checkPosition(self, position):
        ip = self.inStream.tell()
        op = self.outStream.tell()
        if ip != op or ip != position:
            print("IP: %d\tOP: %d\tP: %d" % (ip, op, position))


def decrypt_local(infile, outfile, key, iv):
    with open(infile, 'rb') as src:
        with open(outfile, 'wb') as dest:
            decrypter = AaxDecrypter(src, dest, key, iv)
            decrypter.walk_atoms(Translator(), os.path.getsize(infile))
