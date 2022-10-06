from .parser import arg
from .utils import *


class Book():
  def __init__(self, filename) -> None:
    self.input_filename = filename
    self.bookName = nameFrom(self.input_filename)
    self.book = pullBook(arg('library'), self.bookName)
    self.title = titleFrom(self.book)
    self.final_filename = f"{self.title}.{arg('extension')}"
    self.output_filename = f'.tmp.{self.final_filename}'
    self.metadata_filename = self.input_filename + '.metadata'
    self.updated_metadata_filename = self.metadata_filename + '.new'
    self.acli_metadata_filename = self.input_filename[:self.input_filename.rfind(
        '-')] + '-chapters.json'
    if '.aaxc' in self.input_filename:
        self.voucher = self.input_filename[:self.input_filename.rfind(
            '.aaxc')] + '.voucher'
        keys = aaxcExtrasFrom(self.voucher)
        self.keys = [
            ('-audible_iv', keys['aaxc_iv']),
            ('-audible_key', keys['aaxc_key']),
        ]
    else:
      self.keys = [('-activation_bytes', f'"{bytes()}"')]

  def cleanup(self):
    files = [
        self.output_filename,
        self.metadata_filename,
        self.updated_metadata_filename,
    ]
    command = 'rm -rf'
    for file in files:
      command += f' "{file}"'
    system(command)
