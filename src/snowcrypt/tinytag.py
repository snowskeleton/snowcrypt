#!/usr/bin/env python
# -*- coding: utf-8 -*-

# tinytag - an audio meta info reader
# Copyright (c) 2014-2022 Tom Wallroth
#
# Sources on github:
# http://github.com/devsnd/tinytag/

# MIT License

# Copyright (c) 2014-2022 Tom Wallroth

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


from __future__ import division, print_function
from collections import OrderedDict, defaultdict
try:
    from collections.abc import MutableMapping
except ImportError:
    from collections import MutableMapping
from io import BytesIO
import codecs
import io
import json
import operator
import os
import struct
import sys

# some of the parsers can print debug info
DEBUG = os.environ.get('DEBUG', False)


class TinyTagException(LookupError):  # inherit LookupError for backwards compat
    pass


def stderr(*args):
    sys.stderr.write('%s\n' % ' '.join(repr(arg) for arg in args))
    sys.stderr.flush()


class TinyTag(object):
    def __init__(self, filehandler, filesize, ignore_errors=False):
        self._filehandler = filehandler
        self._filename = None  # for debugging purposes
        self._default_encoding = None  # allow override for some file formats
        self.filesize = filesize
        self.adrmBlob = None  # aax support
        self.album = None
        self.albumartist = None
        self.artist = None
        self.audio_offset = None
        self.bitrate = None
        self.channels = None
        self.checksum = None  # aax support
        self.comment = None
        self.composer = None
        self.disc = None
        self.disc_total = None
        self.duration = None
        self.extra = defaultdict(lambda: None)
        self.genre = None
        self.samplerate = None
        self.bitdepth = None
        self.title = None
        self.track = None
        self.track_total = None
        self.year = None
        self._parse_tags = True
        self._load_image = False
        self._image_data = None
        self._ignore_errors = ignore_errors

    def as_dict(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}

    def get_image(self):
        return self._image_data

    @classmethod
    def get(cls, filename, tags=True, duration=True, image=False, ignore_errors=False,
            encoding=None):
        try:  # cast pathlib.Path to str
            import pathlib
            if isinstance(filename, pathlib.Path):
                filename = str(filename.absolute())
        except ImportError:
            pass
        else:
            filename = os.path.expanduser(filename)
        size = os.path.getsize(filename)
        if not size > 0:
            return TinyTag(None, 0)
        with io.open(filename, 'rb') as af:
            parser_class = MP4
            tag = parser_class(af, size, ignore_errors=ignore_errors)
            tag._filename = filename
            tag._default_encoding = encoding
            tag.load(tags=tags, duration=duration, image=image)
            # turn default dict into dict so that it can throw KeyError
            tag.extra = dict(tag.extra)
            return tag

    def __str__(self):
        return json.dumps(OrderedDict(sorted(self.as_dict().items())))

    def __repr__(self):
        return str(self)

    def load(self, tags, duration, image=False):
        self._parse_tags = tags
        self._load_image = image
        if tags:
            self._parse_tag(self._filehandler)
        if duration:
            if tags:  # rewind file if the tags were already parsed
                self._filehandler.seek(0)
            self._determine_duration(self._filehandler)

    def _set_field(self, fieldname, value, overwrite=True):
        """convenience function to set fields of the tinytag by name"""
        write_dest = self  # write into the TinyTag by default
        get_func = getattr
        set_func = setattr
        # but if it's marked as extra field
        is_extra = fieldname.startswith('extra.')
        if is_extra:
            fieldname = fieldname[6:]
            write_dest = self.extra  # write into the extra field instead
            get_func = operator.getitem
            set_func = operator.setitem
        if get_func(write_dest, fieldname):  # do not overwrite existing data
            return
        if DEBUG:
            stderr('Setting field "%s" to "%s"' % (fieldname, value))
        if fieldname == 'genre':
            genre_id = 255
            if value.isdigit():  # funky: id3v1 genre hidden in a id3v2 field
                genre_id = int(value)
            else:  # funkier: the TCO may contain genres in parens, e.g. '(13)'
                if value[:1] == '(' and value[-1:] == ')' and value[1:-1].isdigit():
                    genre_id = int(value[1:-1])
            if 0 <= genre_id < len(ID3.ID3V1_GENRES):
                value = ID3.ID3V1_GENRES[genre_id]
        if fieldname in ("track", "disc", "track_total", "disc_total"):
            # Converting to string for type consistency
            value = str(value)
        mapping = [(fieldname, value)]
        if fieldname in ("track", "disc"):
            if type(value).__name__ in ('str', 'unicode') and '/' in value:
                value, total = value.split('/')[:2]
                mapping = [(fieldname, str(value)),
                           ("%s_total" % fieldname, str(total))]
        for k, v in mapping:
            if overwrite or not get_func(write_dest, k):
                set_func(write_dest, k, v)

    def _determine_duration(self, fh):
        raise NotImplementedError()

    def _parse_tag(self, fh):
        raise NotImplementedError()

    def update(self, other):
        # update the values of this tag with the values from another tag
        for key in ['track', 'track_total', 'title', 'artist',
                    'album', 'albumartist', 'year', 'duration',
                    'genre', 'disc', 'disc_total', 'comment', 'composer']:
            if not getattr(self, key) and getattr(other, key):
                setattr(self, key, getattr(other, key))

    @staticmethod
    def _unpad(s):
        # strings in mp3 and asf *may* be terminated with a zero byte at the end
        return s.replace('\x00', '')


class MP4(TinyTag):
    # https://developer.apple.com/library/mac/documentation/QuickTime/QTFF/Metadata/Metadata.html
    # https://developer.apple.com/library/mac/documentation/QuickTime/QTFF/QTFFChap2/qtff2.html

    class Parser:
        # https://developer.apple.com/library/mac/documentation/QuickTime/QTFF/Metadata/Metadata.html#//apple_ref/doc/uid/TP40000939-CH1-SW34
        ATOM_DECODER_BY_TYPE = {
            0: lambda x: x,  # 'reserved',
            1: lambda x: codecs.decode(x, 'utf-8', 'replace'),   # UTF-8
            2: lambda x: codecs.decode(x, 'utf-16', 'replace'),  # UTF-16
            3: lambda x: codecs.decode(x, 's/jis', 'replace'),   # S/JIS
            # 16: duration in millis
            13: lambda x: x,  # JPEG
            14: lambda x: x,  # PNG
            21: lambda x: struct.unpack('>b', x)[0],  # BE Signed int
            22: lambda x: struct.unpack('>B', x)[0],  # BE Unsigned int
            23: lambda x: struct.unpack('>f', x)[0],  # BE Float32
            24: lambda x: struct.unpack('>d', x)[0],  # BE Float64
            # 27: lambda x: x,  # BMP
            # 28: lambda x: x,  # QuickTime Metadata atom
            65: lambda x: struct.unpack('b', x)[0],   # 8-bit Signed int
            66: lambda x: struct.unpack('>h', x)[0],  # BE 16-bit Signed int
            67: lambda x: struct.unpack('>i', x)[0],  # BE 32-bit Signed int
            74: lambda x: struct.unpack('>q', x)[0],  # BE 64-bit Signed int
            75: lambda x: struct.unpack('B', x)[0],   # 8-bit Unsigned int
            76: lambda x: struct.unpack('>H', x)[0],  # BE 16-bit Unsigned int
            77: lambda x: struct.unpack('>I', x)[0],  # BE 32-bit Unsigned int
            78: lambda x: struct.unpack('>Q', x)[0],  # BE 64-bit Unsigned int
        }

        @classmethod
        def make_data_atom_parser(cls, fieldname):
            def parse_data_atom(data_atom):
                data_type = struct.unpack('>I', data_atom[:4])[0]
                conversion = cls.ATOM_DECODER_BY_TYPE.get(data_type)
                if conversion is None:
                    stderr('Cannot convert data type: %s' % data_type)
                    return {}  # don't know how to convert data atom
                # skip header & null-bytes, convert rest
                return {fieldname: conversion(data_atom[8:])}
            return parse_data_atom

        @classmethod
        def make_number_parser(cls, fieldname1, fieldname2):
            def _(data_atom):
                number_data = data_atom[8:14]
                numbers = struct.unpack('>HHH', number_data)
                # for some reason the first number is always irrelevant.
                return {fieldname1: numbers[1], fieldname2: numbers[2]}
            return _

        @classmethod
        def parse_id3v1_genre(cls, data_atom):
            # dunno why the genre is offset by -1 but that's how mutagen does it
            idx = struct.unpack('>H', data_atom[8:])[0] - 1
            if idx < len(ID3.ID3V1_GENRES):
                return {'genre': ID3.ID3V1_GENRES[idx]}
            return {'genre': None}

        @classmethod
        def read_extended_descriptor(cls, esds_atom):
            for i in range(4):
                if esds_atom.read(1) != b'\x80':
                    break

        @classmethod
        def parse_audio_sample_entry_mp4a(cls, data):
            # this atom also contains the esds atom:
            # https://ffmpeg.org/doxygen/0.6/mov_8c-source.html
            # http://xhelmboyx.tripod.com/formats/mp4-layout.txt
            # http://sasperger.tistory.com/103
            datafh = BytesIO(data)
            datafh.seek(16, os.SEEK_CUR)  # jump over version and flags
            channels = struct.unpack('>H', datafh.read(2))[0]
            datafh.seek(2, os.SEEK_CUR)   # jump over bit_depth
            datafh.seek(2, os.SEEK_CUR)   # jump over QT compr id & pkt size
            sr = struct.unpack('>I', datafh.read(4))[0]

            # ES Description Atom
            esds_atom_size = struct.unpack('>I', data[28:32])[0]
            esds_atom = BytesIO(data[36:36 + esds_atom_size])
            esds_atom.seek(5, os.SEEK_CUR)   # jump over version, flags and tag

            # ES Descriptor
            cls.read_extended_descriptor(esds_atom)
            esds_atom.seek(4, os.SEEK_CUR)   # jump over ES id, flags and tag

            # Decoder Config Descriptor
            cls.read_extended_descriptor(esds_atom)
            esds_atom.seek(9, os.SEEK_CUR)
            avg_br = struct.unpack('>I', esds_atom.read(4))[0] / 1000  # kbit/s
            return {'channels': channels, 'samplerate': sr, 'bitrate': avg_br}

        @classmethod
        def parse_audio_sample_entry_alac(cls, data):
            # https://github.com/macosforge/alac/blob/master/ALACMagicCookieDescription.txt
            alac_atom_size = struct.unpack('>I', data[28:32])[0]
            alac_atom = BytesIO(data[36:36 + alac_atom_size])
            alac_atom.seek(9, os.SEEK_CUR)
            bitdepth = struct.unpack('b', alac_atom.read(1))[0]
            alac_atom.seek(3, os.SEEK_CUR)
            channels = struct.unpack('b', alac_atom.read(1))[0]
            alac_atom.seek(6, os.SEEK_CUR)
            avg_br = struct.unpack('>I', alac_atom.read(4))[0] / 1000  # kbit/s
            sr = struct.unpack('>I', alac_atom.read(4))[0]
            return {'channels': channels, 'samplerate': sr, 'bitrate': avg_br, 'bitdepth': bitdepth}

        @classmethod
        def parse_mvhd(cls, data):
            # http://stackoverflow.com/a/3639993/1191373
            walker = BytesIO(data)
            version = struct.unpack('b', walker.read(1))[0]
            walker.seek(3, os.SEEK_CUR)  # jump over flags
            if version == 0:  # uses 32 bit integers for timestamps
                walker.seek(8, os.SEEK_CUR)  # jump over create & mod times
                time_scale = struct.unpack('>I', walker.read(4))[0]
                duration = struct.unpack('>I', walker.read(4))[0]
            else:  # version == 1:  # uses 64 bit integers for timestamps
                walker.seek(16, os.SEEK_CUR)  # jump over create & mod times
                time_scale = struct.unpack('>I', walker.read(4))[0]
                duration = struct.unpack('>q', walker.read(8))[0]
            return {'duration': duration / time_scale}

        @classmethod
        def debug_atom(cls, data):
            stderr(data)  # use this function to inspect atoms in an atom tree
            return {}

    # The parser tree: Each key is an atom name which is traversed if existing.
    # Leaves of the parser tree are callables which receive the atom data.
    # callables return {fieldname: value} which is updates the TinyTag.
    META_DATA_TREE = {b'moov': {b'udta': {b'meta': {b'ilst': {
        # see: http://atomicparsley.sourceforge.net/mpeg-4files.html
        # and: https://metacpan.org/dist/Image-ExifTool/source/lib/Image/ExifTool/QuickTime.pm#L3093
        b'\xa9ART': {b'data': Parser.make_data_atom_parser('artist')},
        b'\xa9alb': {b'data': Parser.make_data_atom_parser('album')},
        b'\xa9cmt': {b'data': Parser.make_data_atom_parser('comment')},
        # need test-data for this
        # b'cpil':   {b'data': Parser.make_data_atom_parser('extra.compilation')},
        b'\xa9day': {b'data': Parser.make_data_atom_parser('year')},
        # need test-data for this
        b'\xa9des': {b'data': Parser.make_data_atom_parser('extra.description')},
        b'\xa9gen': {b'data': Parser.make_data_atom_parser('genre')},
        b'\xa9lyr': {b'data': Parser.make_data_atom_parser('extra.lyrics')},
        b'\xa9mvn': {b'data': Parser.make_data_atom_parser('movement')},
        b'\xa9nam': {b'data': Parser.make_data_atom_parser('title')},
        b'\xa9wrt': {b'data': Parser.make_data_atom_parser('composer')},
        b'aART': {b'data': Parser.make_data_atom_parser('albumartist')},
        b'cprt': {b'data': Parser.make_data_atom_parser('extra.copyright')},
        # need test-data for this
        # b'desc': {b'data': Parser.make_data_atom_parser('extra.description')},
        b'disk': {b'data': Parser.make_number_parser('disc', 'disc_total')},
        b'gnre': {b'data': Parser.parse_id3v1_genre},
        b'trkn': {b'data': Parser.make_number_parser('track', 'track_total')},
        # need test-data for this
        # b'tmpo': {b'data': Parser.make_data_atom_parser('extra.bmp')},
    }}}}}

    # see: https://developer.apple.com/library/mac/documentation/QuickTime/QTFF/QTFFChap3/qtff3.html
    AUDIO_DATA_TREE = {
        b'moov': {
            b'mvhd': Parser.parse_mvhd,
            b'trak': {b'mdia': {b"minf": {b"stbl": {b"stsd": {
                b'mp4a': Parser.parse_audio_sample_entry_mp4a,
                b'alac': Parser.parse_audio_sample_entry_alac
            }}}}}
        }
    }

    IMAGE_DATA_TREE = {b'moov': {b'udta': {b'meta': {b'ilst': {
        b'covr': {b'data': Parser.make_data_atom_parser('_image_data')},
    }}}}}

    VERSIONED_ATOMS = {b'meta', b'stsd'}  # those have an extra 4 byte header
    FLAGGED_ATOMS = {b'stsd'}  # these also have an extra 4 byte header
    AAVD_DATA_TREE = {b'aavd': {b'adrm'}}  # unique to audible .aax files

    def _determine_duration(self, fh):
        self._traverse_atoms(fh, path=self.AUDIO_DATA_TREE)

    def _parse_tag(self, fh):
        self._traverse_atoms(fh, path=self.META_DATA_TREE)
        if self._load_image:           # A bit inefficient, we rewind the file
            self._filehandler.seek(0)  # to parse it again for the image
            self._traverse_atoms(fh, path=self.IMAGE_DATA_TREE)

    def _traverse_atoms(self, fh, path, stop_pos=None, curr_path=None):
        header_size = 8
        atom_header = fh.read(header_size)
        while len(atom_header) == header_size:
            atom_size = struct.unpack('>I', atom_header[:4])[0] - header_size
            atom_type = atom_header[4:]
            if curr_path is None:  # keep track how we traversed in the tree
                curr_path = [atom_type]
            if atom_size <= 0:  # empty atom, jump to next one
                atom_header = fh.read(header_size)
                continue
            if DEBUG:
                stderr('%s pos: %d atom: %s len: %d' %
                       (' ' * 4 * len(curr_path), fh.tell() - header_size, atom_type,
                        atom_size + header_size))
            if atom_type in self.VERSIONED_ATOMS:  # jump atom version for now
                fh.seek(4, os.SEEK_CUR)
            if atom_type in self.FLAGGED_ATOMS:  # jump atom flags for now
                fh.seek(4, os.SEEK_CUR)
            sub_path = path.get(atom_type, None)
            # if the path leaf is a dict, traverse deeper into the tree:
            if issubclass(type(sub_path), MutableMapping):
                atom_end_pos = fh.tell() + atom_size
                self._traverse_atoms(fh, path=sub_path, stop_pos=atom_end_pos,
                                     curr_path=curr_path + [atom_type])
            # if the path-leaf is a callable, call it on the atom data
            elif callable(sub_path):
                for fieldname, value in sub_path(fh.read(atom_size)).items():
                    if DEBUG:
                        stderr(' ' * 4 * len(curr_path), 'FIELD: ', fieldname)
                    if fieldname:
                        self._set_field(fieldname, value)
            # Adrm blob described in mov_read_adrm()
            # https://github.com/FFmpeg/FFmpeg/blob/master/libavformat/mov.c
            elif atom_type in self.AAVD_DATA_TREE:
                fh.seek(95, os.SEEK_CUR)  # absolute position 0x251
                self._set_field('adrmBlob', fh.read(56))
                fh.seek(4, os.SEEK_CUR)  # absolute position 0x28d
                self._set_field('checksum', fh.read(20))
            # if we can't figure out what to do with this atom, just skip it and move on
            else:
                fh.seek(atom_size, os.SEEK_CUR)
            # check if we have reached the end of this branch:
            if stop_pos and fh.tell() >= stop_pos:
                return  # return to parent (next parent node in tree)
            atom_header = fh.read(header_size)  # read next atom


class ID3(TinyTag):
    FRAME_ID_TO_FIELD = {  # Mapping from Frame ID to a field of the TinyTag
        'COMM': 'comment', 'COM': 'comment',
        'TRCK': 'track', 'TRK': 'track',
        'TYER': 'year', 'TYE': 'year', 'TDRC': 'year',
        'TALB': 'album', 'TAL': 'album',
        'TPE1': 'artist', 'TP1': 'artist',
        'TIT2': 'title', 'TT2': 'title',
        'TCON': 'genre', 'TCO': 'genre',
        'TPOS': 'disc',
        'TPE2': 'albumartist', 'TCOM': 'composer',
        'WXXX': 'extra.url',
        'TSRC': 'extra.isrc',
        'TXXX': 'extra.text',
        'TKEY': 'extra.initial_key',
        'USLT': 'extra.lyrics',
    }
    ID3V1_GENRES = [
        'Blues', 'Classic Rock', 'Country', 'Dance', 'Disco',
        'Funk', 'Grunge', 'Hip-Hop', 'Jazz', 'Metal', 'New Age', 'Oldies',
        'Other', 'Pop', 'R&B', 'Rap', 'Reggae', 'Rock', 'Techno', 'Industrial',
        'Alternative', 'Ska', 'Death Metal', 'Pranks', 'Soundtrack',
        'Euro-Techno', 'Ambient', 'Trip-Hop', 'Vocal', 'Jazz+Funk', 'Fusion',
        'Trance', 'Classical', 'Instrumental', 'Acid', 'House', 'Game',
        'Sound Clip', 'Gospel', 'Noise', 'AlternRock', 'Bass', 'Soul', 'Punk',
        'Space', 'Meditative', 'Instrumental Pop', 'Instrumental Rock',
        'Ethnic', 'Gothic', 'Darkwave', 'Techno-Industrial', 'Electronic',
        'Pop-Folk', 'Eurodance', 'Dream', 'Southern Rock', 'Comedy', 'Cult',
        'Gangsta', 'Top 40', 'Christian Rap', 'Pop/Funk', 'Jungle',
        'Native American', 'Cabaret', 'New Wave', 'Psychadelic', 'Rave',
        'Showtunes', 'Trailer', 'Lo-Fi', 'Tribal', 'Acid Punk', 'Acid Jazz',
        'Polka', 'Retro', 'Musical', 'Rock & Roll', 'Hard Rock',

        # Wimamp Extended Genres
        'Folk', 'Folk-Rock', 'National Folk', 'Swing', 'Fast Fusion', 'Bebob',
        'Latin', 'Revival', 'Celtic', 'Bluegrass', 'Avantgarde', 'Gothic Rock',
        'Progressive Rock', 'Psychedelic Rock', 'Symphonic Rock', 'Slow Rock',
        'Big Band', 'Chorus', 'Easy Listening', 'Acoustic', 'Humour', 'Speech',
        'Chanson', 'Opera', 'Chamber Music', 'Sonata', 'Symphony', 'Booty Bass',
        'Primus', 'Porn Groove', 'Satire', 'Slow Jam', 'Club', 'Tango', 'Samba',
        'Folklore', 'Ballad', 'Power Ballad', 'Rhythmic Soul', 'Freestyle',
        'Duet', 'Punk Rock', 'Drum Solo', 'A capella', 'Euro-House',
        'Dance Hall', 'Goa', 'Drum & Bass',

        # according to https://de.wikipedia.org/wiki/Liste_der_ID3v1-Genres:
        'Club-House', 'Hardcore Techno', 'Terror', 'Indie', 'BritPop',
        '',  # don't use ethnic slur ("Negerpunk", WTF!)
        'Polsk Punk', 'Beat', 'Christian Gangsta Rap', 'Heavy Metal',
        'Black Metal', 'Contemporary Christian', 'Christian Rock',
        # WinAmp 1.91
        'Merengue', 'Salsa', 'Thrash Metal', 'Anime', 'Jpop', 'Synthpop',
        # WinAmp 5.6
        'Abstract', 'Art Rock', 'Baroque', 'Bhangra', 'Big Beat', 'Breakbeat',
        'Chillout', 'Downtempo', 'Dub', 'EBM', 'Eclectic', 'Electro',
        'Electroclash', 'Emo', 'Experimental', 'Garage', 'Illbient',
        'Industro-Goth', 'Jam Band', 'Krautrock', 'Leftfield', 'Lounge',
        'Math Rock', 'New Romantic', 'Nu-Breakz', 'Post-Punk', 'Post-Rock',
        'Psytrance', 'Shoegaze', 'Space Rock', 'Trop Rock', 'World Music',
        'Neoclassical', 'Audiobook', 'Audio Theatre', 'Neue Deutsche Welle',
        'Podcast', 'Indie Rock', 'G-Funk', 'Dubstep', 'Garage Rock', 'Psybient',
    ]
