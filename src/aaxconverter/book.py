import json
from os import path


class Book():
    def __init__(self, filename) -> None:
        self.filename = filename
        self.outputName = "$(ffmpeg -hide_banner -loglevel quiet " + \
            f"-i {filename} -f ffmetadata -|awk -F'=' -- " + \
            "'/^title/ {print $2}' - | head -1 |sed 's/  / /' |sed 's/ (Unabridged)//').m4a"
        if '.aaxc' in filename:
            self.voucher = filename[:filename.rfind(
                '.aaxc')] + '.voucher'
            if not path.exists(self.voucher):
                raise FileNotFoundError(
                    f"Expecting {self.filename} and {self.voucher} in same directory.")

            keys = self.aaxcExtrasFrom(self.voucher)
            self.keys = [
                ('-audible_iv', keys['aaxc_iv']),
                ('-audible_key', keys['aaxc_key']),
            ]
        else:
            self.keys = [('-activation_bytes', f'"{bytes()}"')]

    def aaxcExtrasFrom(self, voucher):
        with open(voucher, 'r') as file:
            answer = {}
            voucherDict = json.loads(file.read())
            answer['aaxc_key'] = voucherDict['content_license']['license_response']['key']
            answer['aaxc_iv'] = voucherDict['content_license']['license_response']['iv']
            return answer
