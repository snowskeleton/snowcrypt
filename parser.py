# import argparse

# class parse():
#   p = argparse.ArgumentParser(description='Argument parser description')
#   p.add_argument(
#       '--title', '-t',
#       dest='title',
#       type=str,
#       action='store',
#       help='Output filename. Accepts pattern or explicit string. Defaults to filename without junk.',
#       default='',
#   )
#   p.add_argument(
#       '--unattended', '-y',
#       dest='unattended',
#       action='store_true',
#       help='Use default option for all unset values',
#       default='',
#   )
#   p.add_argument(
#       '--extension', '-e',
#       dest='extension',
#       action='store',
#       type=str,
#       help='The output format of your audio files',
#       default='mp3',
#   )
#   p.add_argument(
#     '--input','-i',
#     dest='input',
#     action='store',
#     type=str,
#     default='',
#     help='File to be converted',
#   )
#   p.add_argument(
#     '--silent', '-s',
#     dest='silent',
#     action='store_true',
#     default=False,
#     help='Suppress stdout',
#   )
#   p.add_argument(
#     '--audible-cli-data',
#     dest='audible_cli_data',
#     action='store',
#     help='Filename of library export from mkb79/audible-cli',
#     default='library.tsv',
#   )

#   args = p.parse_args()

#   @classmethod
#   def title(self):
#     return self.args.title

#   @classmethod
#   def unattended(self):
#     return self.args.unattended

#   @classmethod
#   def extension(self):
#     return self.args.extension

#   @classmethod
#   def input(self):
#     return self.args.input

#   @classmethod
#   def silent(self):
#     return self.args.silent

#   @classmethod
#   def audible_cli_data(self):
#     return self.args.audible_cli_data
