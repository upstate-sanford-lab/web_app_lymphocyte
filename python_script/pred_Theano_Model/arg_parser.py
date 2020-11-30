import argparse


class ArgParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def get_args(self):
        self.parser.add_argument("-ip", "--inputpath", help="tile path")
        self.parser.add_argument("-if", "--inputfile", help="tile/svs filename")
        self.parser.add_argument("-o", "--out", help="prediction output path")
        self.parser.add_argument("-gpu", "--gpunum", help="use which GPU")

        args = self.parser.parse_args()
        return args

