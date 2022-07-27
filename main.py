# from parser import parse
import ffmpeg
from utils import tsv2Json
from secretStuff import ACTIVATION_BYTES
import sys


def convert(**kwargs):
  stream = ffmpeg.input(kwargs['input'], activation_bytes=ACTIVATION_BYTES)
  stream = ffmpeg.output(stream, kwargs['output'])
  stream = ffmpeg.overwrite_output(stream)
  stream.run()

if __name__ == "__main__":
  convert(sys.args[1:])