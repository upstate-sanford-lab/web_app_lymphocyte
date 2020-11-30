import argparse


class ArgParser:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def get_args(self):
        # set input and output path
        self.parser.add_argument("-is", "--svs", help="specify input SVS file")
        self.parser.add_argument("-o", "--output", help="specify tile patches output path")
        # set input xml file
        self.parser.add_argument("-ix", "--xml", help="specify input XML file")

        # set magnitude, like zoom ratio 10,20,40 or etc.
        self.parser.add_argument("-mag", "--magnitude", default=20, help="specify magnitude ratio", type=int)
        # set the tile size
        self.parser.add_argument("-ps", "--patchsize", type=int, help="specify the patch image size, like 224*224")

        args = self.parser.parse_args()
        return args

