import unittest
import os
from tests.longStuff import *
from moviepy.editor import AudioFileClip as a_clip


class MyTestCases(unittest.TestCase):

    library_filename = 'testingLibrary.tsv'
    output_filename = 'testingOutput.mp3'
    voucher_filename = 'testingVoucher.voucher'

    def setUp(self) -> None:
        with open(self.library_filename, 'w+') as file:
            file.write(SAMPLE_LIBRARY)
        with open(self.output_filename, 'w+') as file:
            file.write('')
        with open(self.voucher_filename, 'w+') as file:
            file.write(SAMPLE_VOUCHER_TEXT)

        return super().setUp()

    def tearDown(self) -> None:
        os.remove(self.library_filename)
        os.remove(self.output_filename)
        os.remove(self.voucher_filename)

        return super().tearDown()

    def test_readLibrary(self):
        from aaxconverter.utils import readLibrary
        self.assertEqual(readLibrary(self.library_filename), SAMPLE_LIBRARY)

    # def test_convert(self):
    #     from aaxconverter.main import main

    #     for path in [SAMPLE_AAX_FILE_PATH, SAMPLE_AAXC_FILE_PATH]:
    #         # run the conversion with known-good files.
    #         main(input=path, output=self.output_filename)
    #         likelyFile = open(self.output_filename, 'r')
    #         size = os.stat(self.output_filename)

    #         # null check
    #         self.assertIsNot(likelyFile, None)
    #         self.assertGreater(size.st_size, 1)

    #         # this test will fail if output is not able to be imported as an audio file
    #         self.assertTrue(a_clip(self.output_filename))

    # note: this is testing for compatibility with mkb79/audible-cli
    # thus, it may break if audible-cli updates

    def test_pullBook(self):
        from aaxconverter.utils import pullBook
        book = pullBook(self.library_filename, SAMPLE_TITLE)
        simpleBook = pullBook(self.library_filename, SAMPLE_SIMPLE_TITLE)

        self.assertTrue(book)
        self.assertTrue(simpleBook)

        # simple check to make sure the book has some value.
        # if the title is missing, everything else will be missing.
        # if everything is missing, checking the title will catch that
        self.assertTrue(book['title'])
        self.assertTrue(simpleBook['title'])
