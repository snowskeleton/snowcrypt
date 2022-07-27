import unittest
import sys
import os
from tests.longStuff import *
from moviepy.editor import AudioFileClip as a_clip


class MyTestCases(unittest.TestCase):

    library_filename = 'testingLibrary.tsv'
    output_filename = 'testingOutput.mp3'

    def setUp(self) -> None:
        with open(self.library_filename, 'w+') as file:
            file.write(SAMPLE_LIBRARY)
        with open(self.output_filename, 'w+') as file:
            file.write('')

        return super().setUp()

    def tearDown(self) -> None:
        os.remove(self.library_filename)
        os.remove(self.output_filename)

        return super().tearDown()

    def test_readLibrary(self):
        from utils import readLibrary
        self.assertEqual(readLibrary(self.library_filename), SAMPLE_LIBRARY)

    def test_convert(self):
        from main import convert

        # run the conversion with known-good files.
        convert(input=SAMPLE_AAX_FILE_PATH, output=self.output_filename)
        likelyFile = open(self.output_filename, 'r')
        size = os.stat(self.output_filename)

        # null check
        self.assertIsNot(likelyFile, None)
        self.assertGreater(size.st_size, 1)

        # this test will fail if output is not able to be imported as an audio file
        self.assertTrue(a_clip(self.output_filename))

    # note: this is testing for compatibility with mkb79/audible-cli
    # thus, it may break if audible-cli updates

    def test_nameFrom(self):
        from utils import nameFrom
        self.assertEqual(nameFrom("Some_Words_With_Underscors"),
                         "Some Words With Underscors")
        self.assertEqual(nameFrom(
            "Some_Words_Ending_With_A_Dash-thishsouldberemoved.aax"), "Some Words Ending With A Dash")

    def test_pullBook(self):
        from utils import pullBook
        book = pullBook(self.library_filename, SAMPLE_TITLE)
        print(book, "book")

        self.assertTrue(book)
        self.assertTrue(book['title'])

    def test_titleFrom(self):
        from utils import titleFrom
        self.assertEqual(titleFrom(SAMPLE_BOOK), SAMPLE_BOOK_TITLE)

    def test_tsv2json(self):
        from utils import tsv2Json
        self.assertEqual(tsv2Json(SAMPLE_LIBRARY), SAMPLE_LIBRARY_AS_JSON)
