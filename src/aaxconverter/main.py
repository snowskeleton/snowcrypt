import sys
from .parser import arg
from .book import Book
from .decrypt import decrypt_local


def signal_handler(sig, frame):
    sys.exit(print('\naaxConverted: received SIGINT. exiting'))


def main():
    book = Book(arg('input'))
    decrypt_local(book)


if __name__ == "__main__":
    main()
