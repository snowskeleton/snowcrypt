import ffmpeg
from secretStuff import ACTIVATION_BYTES
from parser import parse
from utils import *


def main():
    input = parse.input()
    name = nameFrom(input)
    book = pullBook(parse.audible_cli_data(), name)
    title = titleFrom(book)

    convert(parse.input(), f'{title}.{parse.extension()}')


def convert(input: str, output: str, **kwargs):
  stream = None
  if '.aaxc' in input:
    key = aaxcExtrasFrom(voucherFor(input))['aaxc_key']
    iv = aaxcExtrasFrom(voucherFor(input))['aaxc_iv']
    stream = ffmpeg.input(input, audible_key=key, audible_iv=iv)
  else:
    stream = ffmpeg.input(input, activation_bytes=ACTIVATION_BYTES)
  stream = ffmpeg.output(stream, output, vframes=2)
  stream = ffmpeg.overwrite_output(stream)
  stream.run()


if __name__ == "__main__":
    main()
