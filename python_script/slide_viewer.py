"""Whole Slide Image (WSI) viewer"""
import openslide
from PIL import Image
from matplotlib import pyplot as plt

# this script is running under the flask env path
IMG_PATH = "./static/wsi_png_files/"
SVS_SAVE_PATH = "./static/uploads/wsi_svs_files/"

class WsiViewer:
    def __init__(self, slide_name):
        self.slide_name = slide_name
        self.slide = openslide.OpenSlide(SVS_SAVE_PATH + self.slide_name)

    def show_slide(self):
        """
            Show whole slide img
        """
        print("WSI image: ", self.slide_name)
        thumb = self.slide.get_thumbnail(size=(1000, 1000))
        thumb.save(IMG_PATH + self.slide_name + ".png", format="PNG")
        # thumb.show()

