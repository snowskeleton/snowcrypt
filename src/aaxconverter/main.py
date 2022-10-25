import sys
import os
from .parser import arg
from .book import Book


def signal_handler(sig, frame):
    sys.exit(print('\naaxConverted: received SIGINT. exiting'))


def main():
    book = Book(arg('input'))
    args = [
        ('ffmpeg -loglevel quiet', f"-{arg('overwrite')}"),
        *book.keys,
        ('-i', f'"file:{book.infile}"'),
        ('-c', 'copy'),
        ('-hls_flags', 'temp_file'),
        ('', os.path.join(arg('outputDir'), f'"{book.outfile}"')),
    ]
    os.system(' '.join([f'{arg[0]} {arg[1]}' for arg in args]))


if __name__ == "__main__":
    main()
