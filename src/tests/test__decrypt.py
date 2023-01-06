# this can only run if you have audio files downloaded from mkb79/audible-cli
# import filecmp
# import signal
# import unittest
# from ..snowcrypt.snowcrypt import decrypt_aaxc
# from ..snowcrypt.snowcrypt import decrypt_aax
# from ..snowcrypt.oldcrypt import decrypt_aaxc as old_decrypt_aaxc

# from .constants import *
# from ..snowcrypt.localExceptions import NotDecryptable, DecryptionFailure, NotAnAudibleFile


# def handler(*_):
#     raise TimeoutError()


# contestents = [{
#     'func': decrypt_aaxc,
#     'args': StormAAXC,
#     # 'args': EsperoAAX,
# }, {
#     'func': old_decrypt_aaxc,
#     'args': ControlStormAAXC,
#     # 'args': ControlEsperoAAX,
# }]

# file1 = contestents[0]['args'][1]
# file2 = contestents[1]['args'][1]


# class MyTestCases(unittest.TestCase):
#     def test__same_as_legacy(self):
#         signal.signal(signal.SIGALRM, handler)
#         signal.alarm(30)
#         precryptName1 = 'The_Gathering_Storm_Interview_with_the_Narrators-LC_64_22050_stereo.aax'
#         postcryptName1 = 'The Gathering Storm: Interview with the Narrators.m4a'
#         abytes = 'b2760503'
#         decrypt_aax(precryptName1, postcryptName1, abytes)

#         # control
#         precryptName2 = 'The_Gathering_Storm_Interview_with_the_Narrators-LC_64_22050_stereo.aax'
#         postcryptName2 = 'The Gathering Storm: Interview with the Narrators-control.m4a'
#         key = 'f1c443f8db16304d24edc1245e278eaf'
#         iv = '9024b63436da4986ec5ac1f56729c0e4'

#         old_decrypt_aaxc(precryptName2, postcryptName2, key, iv)

#         if not filecmp.cmp(postcryptName1, postcryptName2):
#             raise EncryptionFailure('Encryption Failed')

#         signal.alarm(0)          # Disable the alarm

#     def test__key_iv_from_file(self):
#         from ..snowcrypt.snowcrypt import key_and_iv_for_file_with_abytes
#         precryptName = 'The_Gathering_Storm_Interview_with_the_Narrators-LC_64_22050_stereo.aax'
#         abytes = 'b2760503'
#         key, iv = key_and_iv_for_file_with_abytes(precryptName, abytes)
#         self.assertIsNotNone(key)
#         self.assertIsNotNone(iv)


# def main():
#     MyTestCases().test__same_as_legacy()


# if __name__ == "__main__":
#     unittest.main()
