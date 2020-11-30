import numpy as np
from openslide import open_slide
from openslide.deepzoom import DeepZoomGenerator
from shapely.geometry import Polygon, Point

from arg_parser import ArgParser
from tile_ops.tile_handler import TileHandler
from patch_savers import *
from tile_ops import tile_handler


class PatchExtractor:
    """
    QX: Patch Extractor
    functions:

    """

    def __init__(self):
        params = ArgParser().get_args()

        self.input_path = params.svs
        # self.input = '/media/mycloud/gdc_download_20200825_162928.797557/TCGA-4Z-AA7Q/TCGA-4Z-AA7Q-01Z-00-DX1.9C30EAED-8DE3-437C-8852-0C64B415AFA8.svs'
        self.xml_file = params.xml
        self.output = params.output
        # the magnitude wanted; like 20x
        self.magnitude = params.magnitude
        self.overlap = 0
        self.patch_size = params.patchsize  # image size of each small patch(sub-tile)

        self.slide = open_slide(self.input_path)  # size of each sub tile, or patch size
        print("[Parameters] \n", params)

    def read_slide(self):
        """ read the whole slide, SVS file
        :arg
        """
        svs_filename = self.input_path.split("/")[-1]
        # create a reader for a specific layer with wanted magnitude
        handler = TileHandler(svs_filename=svs_filename, slide=self.slide, magnitude=self.magnitude,
                             patch_size=self.patch_size, overlap=self.overlap, save_path=self.output)
        handler.get_layer_info()
        # write meta info into lmdb file
        handler.write_meta_info()
        handler.write_all_patches()
        # reader.get_sample_tile(tile_level=16, pos=(123, 133))


if __name__ == '__main__':
    pe = PatchExtractor()
    pe.read_slide()
