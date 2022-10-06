import json
import re
from os import system
from .config import bytes


def tsv2Json(input_text) -> dict:
    answer = []

    # convert from string into list, with each newline as an entry
    rows = input_text.split('\n')
    # pop off the first of the rows, which is the headers. saved for later.
    headers = rows.pop(0).split('\t')

    for row in rows:
        # for some reason, nearly-empty rows like
        # to sneak in occasionally. skip them.
        if len(row) < 2:
            continue
        entry = {}

        for header, value in zip(headers, row.split('\t')):
            entry[header] = value.strip()
        answer.append(entry)

    return answer


def readLibrary(libraryFilename: str = 'library.tsv'):
    with open(libraryFilename, 'r') as file:
        return file.read()

# returns the first book matching provided title from provided library
# uses mkb79/audible-cli default naming scheme '$title $subtitle'


def pullBook(library, requestedTitle):
    for book in tsv2Json(readLibrary(library)):
        title = f"{book['title']} {book['subtitle']}"
        if clean(title) == clean(requestedTitle):
            return book
        if clean(book['title']) == clean(requestedTitle):
            return book


def clean(string):
    return re.sub(r'[^a-zA-Z]', '', string)


def nameFrom(file):
    name = file.replace('_', ' ')
    index = name.rfind('-')
    return name[:index] if index != -1 else name


def voucherFor(file):
    return f"{file.rsplit('.aaxc', 1)[0]}.voucher"


def titleFrom(book: dict):
    if book['subtitle'] == '':
        return book['title']
    return f"{book['title']}: {book['subtitle']}"


def chaptersFrom(file: str):
    """
        change 'foo-bar' to 'foo-chapters.json'
    """
    return file[:file.rfind('-')] + "-chapters.json"


def aaxcExtrasFrom(voucher):
    with open(voucher, 'r') as file:
        answer = {}
        voucherDict = json.loads(file.read())
        answer['aaxc_key'] = voucherDict['content_license']['license_response']['key']
        answer['aaxc_iv'] = voucherDict['content_license']['license_response']['iv']
        return answer


def execute(command, arguments):
  for arg in arguments:
    command += f' {arg[0]} {arg[1]}'
  system(command)


def authExtras(audioFile):
    if '.aaxc' in audioFile:
        keys = aaxcExtrasFrom(voucherFor(audioFile))
        return [
            ('-audible_iv', keys['aaxc_iv']),
            ('-audible_key', keys['aaxc_key']),
        ]
    return [('-activation_bytes', f'"{bytes()}"')]
