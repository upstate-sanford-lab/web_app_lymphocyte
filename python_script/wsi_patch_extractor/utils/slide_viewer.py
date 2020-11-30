"""Whole Slide Image (WSI) viewer"""
import openslide
from PIL import Image
from matplotlib import pyplot as plt


class WsiViewer:
    def __init__(self, slide_img):
        self.slide = openslide(slide_img)

    def show_slide(self):
        """
            Show whole slide img
        """
        print("WSI image:")
