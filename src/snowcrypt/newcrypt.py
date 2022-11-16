# https://github.com/mkb79/Audible/issues/36, user BlindWanderer
from io import BufferedReader, BufferedWriter
import struct
from Crypto.Cipher import AES
import os
import sys


ints = {
    (0,  0x4D344120),  # "M4A "
    (4,  0x00000200),  # version 2.0?
    (8,  0x69736F32),  # "iso2"
    (12, 0x4D344220),  # "M4B "
    (16, 0x6D703432),  # "mp42"
    (20, 0x69736F6D),  # "isom"
}


class Stream:
    def __init__(self) -> None:
        self.end = None
        self.input = None
        self.output = None
        self.translator = Translator()

    def saveStart(self):
        self.start = self.input.tell()

    def notEnded(self):
        x = self.input.tell() < self.end
        return x

    def log(self, fileSize):
        pass

    def resetTranslator(self):
        self.translator.reset()


class Atom:

    def __init__(self) -> None:
        self.position: int = None
        self.start: int = None
        self.end: int = None
        self.atomType: int = None
        self.typePosition: int = None
        self.type: int = None
        self.length: int = None


class Translator:
    fshort = (">h", 2)
    fint = (">i", 4)
    flong = (">q", 8)

    def __init__(self, size=None):
        self.buf = bytearray(size if size != None else 4096)
        self.pos = 0
        self.wpos = 0

    def reset(self):
        self.pos = 0
        self.wpos = 0

    def position(self): return self.pos
    def getShort(self): return self.getOne(self.fshort)
    def getInt(self): return self.getOne(self.fint)
    def getLong(self): return self.getOne(self.flong)

    def putInt(self, position, value):
        self.putOne(self.fint, position, value)

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
        if (atomLength == 1):  # 64 bit atom!
            atomLength = Translator.readLong(inStream)
        return atomLength

    def zero(self, start=0, end=None):
        if end == None:
            end = self.wpos
        for i in range(start, end):
            self.buf[i] = 0

    def write_and_reset(self, outStream) -> int:
        r = self.write(outStream)
        self.reset()
        return r


class AaxDecrypter:
    filetypes = {6: "html", 7: "xml", 12: "gif",
                 13: "jpg", 14: "png", 15: "url", 27: "bmp"}

    def __init__(self, infile, outfile, key, iv):
        self.key = bytes.fromhex(key)
        self.iv = bytes.fromhex(iv)
        self.source = infile
        self.dest = outfile
        self.filesize = os.path.getsize(infile)

    # def walk_ilst(self, translator, inStream, outStream, endPosition):  # cover extractor
    #     startPosition = inStream.tell()
    #     while inStream.tell() < endPosition:
    #         translator.reset()
    #         self.status(inStream.tell(), self.filesize)
    #         atomStart = inStream.tell()
    #         atomLength = translator.readAtomSize(inStream)
    #         atomEnd = atomStart + atomLength
    #         atom = translator.readInt(inStream)
    #         remaining = atomLength - translator.write_and_reset(outStream)

    #         if (atom == 0x636F7672):  # covr
    #             #Going to assume ONE data atom per item.
    #             # dataLength = translator.readAtomSize(inStream)
    #             translator.readInto(inStream, 12)
    #             translator.skipInt()  # data
    #             # type = translator.getInt()  # type
    #             translator.skipInt()  # zero?
    #             remaining = remaining - translator.write_and_reset(outStream)
    #             # if type in self.filetypes:
    #             #     postfix = self.filetypes[type]
    #             #     uk = self.dest.with_suffix(
    #             #         ".embedded-cover." + postfix)
    #             #     with open(uk, 'wb') as cover:
    #             #         remaining = remaining - \
    #             #             self.copy(inStream, remaining, outStream, cover)

    #         if (remaining > 0):
    #             walked = False
    #             self.copy(inStream, remaining, outStream)
    #         self.checkPosition(inStream, outStream, atomEnd)

    #     self.status(inStream.tell(), self.filesize)
    #     return endPosition - startPosition

    def walk_mdat(self, inStream, outStream, _, translator, endPosition):  # samples
        startPosition = inStream.tell()
        # It's illegal for mdat to contain atoms... but that didn't stop Audible! Not that any parsers care.
        # while inStream.tell() < endPosition
        while inStream.tell() < endPosition:
            print('mdat')
            # self.status(inStream.tell(), self.filesize)
            # read an atom length.
            atom = Atom()
            atom.start = inStream.tell()
            # atomStart = inStream.tell()
            translator.reset()
            atom.length = translator.readAtomSize(inStream)
            # atomLength = translator.readAtomSize(inStream)
            atom.typePosition = translator.position()
            atom.type = translator.readInt(inStream)

            # after the atom type comes 5 additional fields describing the data.
            # We only care about the last two.
            translator.readInto(inStream, 20)
            translator.skipInt()  # time in ms
            translator.skipInt()  # first block index
            translator.skipInt()  # trak number
            totalBlockSize = translator.getInt()  # total size of all blocks
            blockCount = translator.getInt()  # number of blocks

            # atom.end = atom.start + atom.length + totalBlockSize
            # atomEnd = atomStart + atomLength + totalBlockSize

            # next come the atom specific fields
            # aavd has a list of sample sizes and then the samples.
            if (atom.type == nameToHex['aavd']):
                print('you haven\'t gotten here yet')

                translator.putInt(
                    atom.typePosition, nameToHex['mp4a']['hex'])  # mp4a
                translator.readInto(inStream, blockCount * 4)
                translator.write(outStream)
                for _ in range(blockCount):
                    self.status(inStream.tell(),  self.filesize)
                    sampleLength = translator.getInt()
                    # has to be reset every go round.
                    cipher = AES.new(self.key, AES.MODE_CBC, iv=self.iv)
                    remaining = sampleLength - \
                        outStream.write(cipher.decrypt(
                            inStream.read(sampleLength & 0xFFFFFFF0)))
                    # fun fact, the last few bytes of each sample aren't encrypted!
                    if remaining > 0:
                        AaxDecrypter.copy(inStream, remaining, outStream)
            # there is no point in actually parsing this,
            # we would need to rebuild the sample tables if we wanted to modify it.
            # elif atomType == 0x74657874: #text
            #    translator.readInto(inStream, bc * 2)
            #    translator.write(outStream)
            #    for i in range(bc):
            #        sampleLength = translator.getShort()
            #        t2 = Translator(sampleLength * 2)
            #        t2.readInto(inStream, sampleLength)
            #        t2.getString(sampleLength)
            #        before = t2.readCount()
            #        encdSize = t2.readAtomSize(inStream)#encd atom size
            #        t2.readInto(inStream, encdSize + before - translator.readCount())
            #        t2.write(outStream)
            #    translator.reset()
            else:
                len = translator.write_and_reset(outStream)
                AaxDecrypter.copy(inStream, atom.length +
                          totalBlockSize - len, outStream)
            translator.reset()
            # self.checkPosition(inStream, outStream,
            #                    atom.end - atom.length)

        return endPosition - startPosition

    def walk_atoms(self, inStream, outStream, translator, endPosition):  # everything
        start = inStream.tell()
        while inStream.tell() < endPosition:
            # print(endPosition - inStream.tell())
            # self.status(inStream.tell(), self.filesize)
            # read an atom length.
            translator.reset()
            atom = Atom()
            start = inStream.tell()
            length = translator.readAtomSize(inStream)
            atom.start, atom.length, end = start, length, start + length
            remains = atom.length
            atom.position = translator.position()
            atom.atomType = translator.readInt(inStream)
            # try:
            #     print(
            #         f"a-type: {atom.atomType}\n"
            #         f"hextoname: {hexToName[atom.atomType]}\n"
            #     )
            # except:
            #     print(f"a-type: {atom.atomType}\n")

            try:
                datum = hexToName[atom.atomType]
                print(datum['name'])
                func = datum['func']
                remains = func(inStream, outStream, atom, translator, remains)
            except KeyError:
                remains = remains - \
                    translator.write_and_reset(outStream)
                AaxDecrypter.copy(inStream, remains, outStream)

            # don't care about the children.

            AaxDecrypter.checkPosition(inStream, outStream, end)

        # stream.log(self.filesize)
        return endPosition - start

    def status(self, position, filesize):
        None

    def copy(inStream, length, *outs) -> int:
        remaining = length
        while remaining > 0:
            remaining = remaining - \
                AaxDecrypter.write(inStream.read(
                    min(remaining, 4096)), *outs)
        return length

    def write(buf, *outs) -> int:
        [out.write(buf) for out in outs]
        return len(buf)

    def checkPosition(inStream, outStream, position):
        ip, op = inStream.tell(), outStream.tell()
        if ip != op or ip != position:
            print("IP: %d\tOP: %d\tP: %d" % (ip, op, position))

    @classmethod
    def case_aavd(cls, inStream, outStream, atom: Atom, translator: Translator, remains):
        translator.putInt(atom.position, nameToHex['mp4a']['hex'])  # mp4a
        remains = remains - translator.write_and_reset(outStream)
        # don't care about the children.
        AaxDecrypter.copy(inStream, remains, outStream)
        return remains

    @classmethod
    def case_moov(cls, inStream, outStream, _, translator: Translator, remains):
        remains = remains - translator.write_and_reset(outStream)
        return remains - AaxDecrypter.walk_atoms(cls, inStream, outStream, translator, remains)

    @classmethod  # pass to case_moov
    def case_mdia(cls, inStream, outStream, _, translator: Translator, remains):
        return AaxDecrypter.case_moov(inStream, outStream, None, translator, remains)

    @classmethod  # pass to case_moov
    def case_minf(cls, inStream, outStream, _, translator: Translator, remains):
        return AaxDecrypter.case_moov(inStream, outStream, None, translator, remains)

    @classmethod  # pass to case_moov
    def case_stbl(cls, inStream, outStream, _, translator: Translator, remains):
        return AaxDecrypter.case_moov(inStream, outStream, None, translator, remains)

    @classmethod  # pass to case_moov
    def case_trak(cls, inStream, outStream, _, translator: Translator, remains):
        return AaxDecrypter.case_default(inStream, outStream, None, translator, remains)

    @classmethod  # pass to case_moov
    def case_udta(cls, inStream, outStream, _, translator: Translator, remains):
        return AaxDecrypter.case_moov(inStream, outStream, None, translator, remains)

    @classmethod
    def case_stsd(cls, inStream, outStream, _, translator: Translator, remains):
        translator.readInto(inStream, 8)
        remains = remains - translator.write_and_reset(outStream)
        return remains - cls.walk_atoms(inStream, outStream, remains, translator)

    @classmethod
    def case_meta(cls, inStream, outStream, _, translator: Translator, remains):
        translator.readInto(inStream, 4)
        remains = remains - \
            translator.write_and_reset(outStream)
        return remains - AaxDecrypter.walk_atoms(cls, inStream, outStream, translator, remains)

    @classmethod
    def case_ftyp(cls, inStream, outStream, _, translator: Translator, remains):
        remains = remains - \
            translator.write_and_reset(outStream)
        len = translator.readInto(inStream, remains)
        [translator.putInt(loca, value) for loca, value in ints]
        translator.zero(24, len)
        return remains - translator.write_and_reset(outStream)

    @classmethod
    def case_mdat(cls, inStream, outStream, _, translator: Translator, remains):
        # remaining = remaining - translator.write_and_reset(outStream)
        # remaining = remaining - \
        #     self.walk_mdat(translator, inStream,
        #                     outStream, atomEnd)
        remains = remains - translator.write_and_reset(outStream)
        return remains - AaxDecrypter.walk_mdat(cls, inStream, outStream, None, translator, remains)

    @classmethod
    def case_default(cls, inStream, outStream, _, translator, remains):
        remains = remains - translator.write_and_reset(outStream)
        return remains - AaxDecrypter.copy(inStream, remains, outStream)


def decrypt_local(infile, outfile, key, iv):
    with open(infile, 'rb') as input:
        with open(outfile, 'wb') as output:
            decrypter = AaxDecrypter(infile, outfile, key, iv)
            decrypter.walk_atoms(
                input, output, Translator(), decrypter.filesize)


# def atomizer(stream):
#     start = inStream.tell()
#     length = translator.readAtomSize(inStream)
#     end = start + length
#     return length, end


nameToHex = {
    'aavd':   {
        'hex': 0x61617664,
        'func': AaxDecrypter.case_aavd
    },
    'mp4a':   {
        'hex': 0x6d703461,
        'func': AaxDecrypter.case_default
    },
    'moov-0': {
        'hex': 0x6d6f6f76,
        'func': AaxDecrypter.case_moov
    },
    'trak-0': {
        'hex': 0x7472616b,
        'func': AaxDecrypter.case_trak
    },
    'mdia-0': {
        'hex': 0x6d646961,
        'func': AaxDecrypter.case_mdia
    },
    'minf-0': {
        'hex': 0x6d696e66,
        'func': AaxDecrypter.case_minf
    },
    'stbl-0': {
        'hex': 0x7374626c,
        'func': AaxDecrypter.case_stbl
    },
    'udta-0': {
        'hex': 0x75647461,
        'func': AaxDecrypter.case_udta
    },
    'meta-4': {
        'hex': 0x6D657461,
        'func': AaxDecrypter.case_meta
    },
    'stsd-8': {
        'hex': 0x73747364,
        'func': AaxDecrypter.case_stsd
    },
    'ftyp-none': {
        'hex': 0x66747970,
        'func': AaxDecrypter.case_ftyp
    },
    'mdat-none': {
        'hex': 0x6d646174,
        'func': AaxDecrypter.case_mdat
    }
}

hexToName = {
    0x61617664: {
        'name': 'aavd',
        'func': AaxDecrypter.case_aavd
    },
    0x6d703461: {
        'name': 'mp4a',
        'func': AaxDecrypter.case_default
    },
    0x6d6f6f76: {
        'name': 'moov-0',
        'func': AaxDecrypter.case_moov
    },
    0x7472616b: {
        'name': 'trak-0',
        'func': AaxDecrypter.case_trak
    },
    0x6d646961: {
        'name': 'mdia-0',
        'func': AaxDecrypter.case_mdia
    },
    0x6d696e66: {
        'name': 'minf-0',
        'func': AaxDecrypter.case_minf
    },
    0x7374626c: {
        'name': 'stbl-0',
        'func': AaxDecrypter.case_stbl
    },
    0x75647461: {
        'name': 'udta-0',
        'func': AaxDecrypter.case_udta
    },
    0x6D657461: {
        'name': 'meta-4',
        'func': AaxDecrypter.case_meta
    },
    0x73747364: {
        'name': 'stsd-8',
        'func': AaxDecrypter.case_stsd
    },
    0x66747970: {
        'name': 'ftyp-none',
        'func': AaxDecrypter.case_ftyp
    },
    0x6d646174: {
        'name': 'mdat-none',
        'func': AaxDecrypter.case_mdat
    },
    0x00000000: {
        'name': 'default',
        'func': AaxDecrypter.case_default
    }
}
