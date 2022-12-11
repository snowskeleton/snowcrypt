# this can only run if you have audio files downloaded from mkb79/audible-cli
# import filecmp
# import signal
# import unittest
# from ..snowcrypt.snowcrypt import decrypt_aaxc as newcrypt
# from ..snowcrypt.oldcrypt import decrypt_aaxc as oldcrypt

# from .constants import *
# from ..snowcrypt.localExceptions import NotDecryptable


# def handler(*_):
#     raise NotDecryptable()


# contestents = [{
#     'func': newcrypt,
#     'args': StormAAXC,
#     # 'args': EsperoAAX,
# }, {
#     'func': oldcrypt,
#     'args': ControlStormAAXC,
#     # 'args': ControlEsperoAAX,
# }]

# file1 = contestents[0]['args'][1]
# file2 = contestents[1]['args'][1]


# class MyTestCases(unittest.TestCase):
#     def test__same_as_legacy(self):
#         try:
#             signal.signal(signal.SIGALRM, handler)
#             signal.alarm(5)
#             one, two = race(contestents, 1)
#             if not filecmp.cmp(file1, file2):
#                 raise EncryptionFailure('Encryption Failed')

#             one = str(one)[:5]
#             two = str(two)[:5]
#             print('new : ', one)
#             print('old : ', two)
#         except NotDecryptable:
#             print('Decryption took too long')
#         except KeyboardInterrupt:
#             print('\nReceived escape sequence')
#         finally:
#             signal.alarm(0)          # Disable the alarm


# def main():
#     MyTestCases().test__same_as_legacy()


# if __name__ == "__main__":
#     unittest.main()
