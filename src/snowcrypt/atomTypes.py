from enum import IntEnum


class TYPES(IntEnum):
  AAVD: int = 0x61617664
  MP4A: int = 0x6d703461
  MOOV: int = 0x6d6f6f76
  TRAK: int = 0x7472616b
  MDIA: int = 0x6d646961
  MINF: int = 0x6d696e66
  STBL: int = 0x7374626c
  UDTA: int = 0x75647461
  META: int = 0x6D657461
  STSD: int = 0x73747364
  FTYP: int = 0x66747970
  MDAT: int = 0x6d646174
  ISO2: int = 0x69736F32
  MP42: int = 0x6D703432
  ISOM: int = 0x69736F6D
  M4A: int = 0x4D344120
  M4B: int = 0x4D344220
  VERSION2_0: int = 0x00000200
