AAVD: int = 0x61617664
FTYP: int = 0x66747970
ISO2: int = 0x69736F32
ISOM: int = 0x69736F6D
M4A: int = 0x4D344120
M4B: int = 0x4D344220
MDAT: int = 0x6d646174
MDIA: int = 0x6d646961
META: int = 0x6D657461
MINF: int = 0x6d696e66
MOOV: int = 0x6d6f6f76
MP42: int = 0x6D703432
MP4A: int = 0x6d703461
STBL: int = 0x7374626c
STSD: int = 0x73747364
TRAK: int = 0x7472616b
UDTA: int = 0x75647461
VERSION2_0: int = 0x00000200
BULK_ATOMS = [MOOV, TRAK, MDIA, MINF, STBL, UDTA]
FTYP_TAGS = [M4A, VERSION2_0, ISO2, M4B, MP42, ISOM]
ADRM_START: int = 0x251
ADRM_LENGTH: int = 56
CKSM_START: int = 0x28d
CKSM_LENGTH: int = 20
FIXEDKEY = bytes.fromhex('77214d4b196a87cd520045fd20a51d67')
