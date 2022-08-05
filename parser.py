import argparse


class parse():

    inited = False

    extension = None
    unattended = None
    input = None
    output = None
    silent = None
    audible_cli_data = None

    
    def firstRun(self):
        self.p = argparse.ArgumentParser(description='Argument parser description')
        self.p.add_argument(
            '--unattended', '-y',
            dest='unattended',
            action='store_true',
            help='Use default option for all unset values',
            default='',
        )
        self.p.add_argument(
            '--extension', '-e',
            dest='extension',
            action='store',
            type=str,
            help='The output format of your audio files',
            default='mp3',
        )
        self.p.add_argument(
            '--input', '-i',
            dest='input',
            action='store',
            type=str,
            help='File to be converted',
            default='',
        )
        self.p.add_argument(
            '--output', '-o',
            dest='output',
            type=str,
            action='store',
            help='Output filename. Accepts pattern or explicit string. Defaults to filename without junk.',
            default='',
        )
        self.p.add_argument(
            '--silent', '-s',
            dest='silent',
            action='store_true',
            default=False,
            help='Suppress stdout',
        )
        self.p.add_argument(
            '--audible-cli-data',
            dest='audible_cli_data',
            action='store',
            help='Filename of library export from mkb79/audible-cli',
            default='library.tsv',
        )
        self.args = self.p.parse_args()

        self.extension = self.args.extension
        self.input = self.args.input
        self.output = self.args.output
        self.audible_cli_data = self.args.audible_cli_data
        self.silent = self.args.silent
        self.unattended = self.args.unattended
        

    # # catchall
    # self.p.add_argument(dest='rest', nargs=argparse.REMAINDER)


    @classmethod
    def extension(self):
        return self.args.extension

    @classmethod
    def autoYes(self):
        return self.args.unattended

    @classmethod
    def input(self):
        return self.args.input

    @classmethod
    def output(self):
        return self.args.output

    @classmethod
    def silent(self):
        return self.args.silent

    @classmethod
    def audible_cli_data(self):
        return self.args.audible_cli_data
    
    # @classmethod
    # def remainder(self):
    #     return self.args.rest
