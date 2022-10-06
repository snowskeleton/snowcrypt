from os import system
from .parser import arg
from .utils import *
from book import Book


def main():
  book = Book(arg('input'))
  system(
      f'ffmpeg -y -i "{book.input_filename}" -f ffmetadata "{book.metadata_filename}"')

  from .update_chapter_titles import main
  try:
    main([
        '--ffmeta', f'{book.metadata_filename}',
        '--apimeta', f'{book.acli_metadata_filename}',
        '--outfile', f'{book.updated_metadata_filename}',
    ])
  except:
    pass  # above likes to crash after completing.

  args = [
      # different keys depending on .aax vs .aaxc
      *book.keys,
      ('-i', f'"{book.input_filename}"'),
      # ('-f', f'ffmetadata'), ('-i', f'"{book.updated_metadata_filename}"'),
      # audio and video (artwork) from audio
      # ('-map', '0:a'), ('-map', '0:v'),
      # metadata and chapters from metadata
      # ('-map_metadata', '1'), ('-map_chapters', '1'),
      ('-vframes 1', f'"{book.output_filename}"'),
  ]

  execute('ffmpeg -y -nostats ', args)
  execute(
      'mv -f', [(
          f'"{book.output_filename}"',
          f'"{book.final_filename}"',
      )])
  book.cleanup()


if __name__ == "__main__":
    main()
