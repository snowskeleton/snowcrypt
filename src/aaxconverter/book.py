import json
from os import path
from .tinytag import TinyTag
from dataclasses import dataclass, field


@dataclass
class Book():

    infile: str
    iv: str = field(init=False)
    key: str = field(init=False)
    keys: list = field(init=False)
    title: str = field(init=False)
    outfile: str = field(init=False)
    voucher: str = field(init=False)
    tags: TinyTag = field(init=False)
    description: str = field(init=False)

    def __post_init__(self):
        self.tags = TinyTag.get(self.infile, encoding='MP4')
        self.outfile = f"{self.tags.title.replace(' (Unabridged)', '')}.m4a"
        if '.aaxc' not in self.infile:
            self.keys = [('-activation_bytes', f'"{bytes()}"')]
            self.voucher = None
        else:
            self.voucher = self.infile.replace('.aaxc', '.voucher')
            if not path.exists(self.voucher):
                raise FileNotFoundError(
                    f"Oops, {self.infile} and {self.voucher} not together.")

            keys = self.aaxcExtrasFrom(self.voucher)
            self.iv = keys['aaxc_iv']
            self.key = keys['aaxc_key']
            self.keys = [
                ('-audible_iv', self.iv),
                ('-audible_key', self.key),
            ]

    def aaxcExtrasFrom(self, voucher):
        with open(voucher, 'r') as file:
            answer = {}
            voucherDict = json.loads(file.read())
            answer['aaxc_key'] = voucherDict['content_license']['license_response']['key']
            answer['aaxc_iv'] = voucherDict['content_license']['license_response']['iv']
            return answer
