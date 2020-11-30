import argparse


class ArgParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def get_args(self):
        self.parser.add_argument("-s", "--slide", help="slide full path")
        self.parser.add_argument("-p", "--pred", help="pred file path")
        self.parser.add_argument("-x", "--xml", help="xml file for WSI roi annotation")
        self.parser.add_argument("-o", "--out", help="heatmap output path")
        self.parser.add_argument("-lp", "--lmdbpath", help="lmdb tiles path")
        self.parser.add_argument("-lf", "--lmdbfilename", help="lmdb file name")

        args = self.parser.parse_args()
        return args

