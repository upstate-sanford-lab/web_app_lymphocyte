from PIL import Image
import openslide
from openslide.deepzoom import DeepZoomGenerator

from helper import *
from tqdm import tqdm
import os
import time
from joblib import Parallel, delayed

import patch_savers


class TileHandler:
    def __init__(self, svs_filename, slide, magnitude, patch_size, overlap, save_path):
        """
        :arg
            -   slide: the WSI from SVS file
            -   tile_size: the size of each sub tile, like 300*300, 100*100, 224*224 and etc.
            -   overlap:
            -   wanted_mag: wanted magnitude of a level, like 10x,20x,40x
            -   tiles: Tiles object generated from DeepZoom, contains all sub tiles
        """
        self.svs_filename = svs_filename
        self.slide = slide
        self.patch_size = patch_size
        self.overlap = overlap
        self.wanted_mag = magnitude
        self.save_path = save_path
        # tiles from DeepZoom;
        # #for deciding wanted zoom ratio at which level of slide image (like 20x is at base level in slide)
        self.deepzoom_tiles = DeepZoomGenerator(self.slide, self.patch_size, self.overlap)
        self.level_count = self.deepzoom_tiles.level_count
        # create tiles_saver object, save all extracted tiles
        self.patch_saver = patch_savers.LmdbSaver(save_path=self.save_path, filename=self.svs_filename)

    def get_layer_info(self):
        """ get the info for a specific layer with wanted magnitude; like a layer with '40x' mag
        :arg
        :returns
            -   slide_level_num: want magnitude is which level; like 20x at level 0
            -   X_pixels, Y_pixels: slide layer x,y pixel size
            -   patch_size_at_layer: the real size(pixels) of each patch at corresponding slide layer
        """
        # list of all magnitudes corresponding to all layers
        all_mags_list, mag_slide_layer_dict, patch_size_at_layer = self.get_layer_mag_dim()
        if __debug__:  # set DEBUG mode as cmd: python -d your_program.py; "python -O" to disable debug mode
            print("[DEBUG INFO]: ",
                  '\n', "All Magnitudes at different layer", all_mags,
                  '\n', "magnitude for which slide layer list", mag_slide_layer_dict)

        # get level number in slide, corresponding to wanted magnitude
        # base level is level 0, there are always 4 levels in a slide object
        slide_level_num = mag_slide_layer_dict[self.wanted_mag]
        # get total pixel nums at X and Y axis
        X_pixels, Y_pixels = self.slide.level_dimensions[slide_level_num]
        print("[INFO]: ",
              '\n --- Wanted Magnitude:{}; At Slide Level:{}; with Size(pixels): Width(X)={} Height(Y)={}'
              .format(self.wanted_mag, slide_level_num, X_pixels, Y_pixels),
              '\n --- Extract Patch size:{}; Real size of each patch at {}-th slide Level:{}'
              .format(self.patch_size, slide_level_num, patch_size_at_layer))
        return slide_level_num, X_pixels, Y_pixels, patch_size_at_layer

    def get_layer_mag_dim(self):
        """ get magnitude, and pixel dimension at different layer
        :arg
            None
        :returns
            -   all_mags_list: list of magnitude at different layer
            -   mag_layer_dict:
            -   patch_size_at_layer: the real size of a patch at slide layer;
                e.p: 100*100 extracted patch is 203*203 at slide level 0
        """
        # physical micros per pixel at x,y direction
        mmp_x = self.slide.properties[openslide.PROPERTY_NAME_MPP_X]
        mmp_y = self.slide.properties[openslide.PROPERTY_NAME_MPP_Y]
        if mmp_x != mmp_y:
            print("[WARNING]\n --- The micros per pixel at X & Y axis are different!")

        # physical magnitude, or acquisition mag
        phy_mag = 10.0 / float(mmp_x)
        base_mag = int(20 * round(float(phy_mag) / 20))
        print("[INFO]:" "\n --- Physical Magnitude: {}; Base Magnitude: {}".format(phy_mag, base_mag),
              "\n --- Total slide layer count: ", self.slide.level_count)

        # REAL PIXEL SIZE AT SLIDE LAYER OF EACH PATCH
        patch_size_at_layer = int(self.patch_size * phy_mag / self.wanted_mag)

        # down samples
        l_z_ds = self.deepzoom_tiles._l_z_downsamples
        l0_l_ds = self.deepzoom_tiles._l0_l_downsamples
        dz_level = self.deepzoom_tiles._slide_from_dz_level
        if __debug__:  # set DEBUG mode as cmd: python -d your_program.py
            print("[DEBUG INFO]: ", '\n', l_z_ds, '\n', l0_l_ds, '\n', dz_level)

        # equation for computing all magnitudes corresponding layer
        all_mags_list = tuple(
            base_mag / (l_z_ds[i] * l0_l_ds[dz_level[i]])
            for i in range(0, self.level_count)
        )
        # mag_layer_dict is a dictionary like: {magnitude:layer_num}
        mag_layer_dict = {all_mags_list[i]: dz_level[i] for i in range(len(all_mags_list))}
        return all_mags_list, mag_layer_dict, patch_size_at_layer

    def get_sample_tile(self, tile_level, pos):
        """ Show a sample image of a tile
        :arg
            -   tiles: all tiles extracted from DeepZoom
            -   mag: magnitude ratio, like 10,20,40 and etc.
            -   pos: {tile_x, tile_y}
                tile_x: x num of tile
                tile_y: y num of tile
        :return
            none: nothing for now
        """
        print("[INFO]:\n --- show tile image at: LEVEL={0} x={1}, y={2}".format(tile_level, pos[0], pos[1]))
        tile_image = self.deepzoom_tiles.get_tile(tile_level, pos)
        tile_image.show()

    def write_meta_info(self):
        """ Write tiles meta info to lmdb file
        """
        slide_level_num, X_pixels, Y_pixels, patch_on_slide_size = self.get_layer_info()
        meta_info = {'slide_level_num': slide_level_num, 'patch_on_slide_size': patch_on_slide_size,
                     'slide_X_pixels': X_pixels, 'slide_Y_pixels': Y_pixels}
        self.patch_saver.write_meta(meta_info)

    def write_all_patches(self):
        """ Generate all tiles at layer with wanted magnitude"""
        start = time.time()
        print("[INFO]: generate all tiles")
        slide_level_num, X_pixels, Y_pixels, patch_size_at_layer = self.get_layer_info()

        n_threads = os.cpu_count()
        print("[INFO]:\n --- {0} logical CPU cores detected, create {1} writing threads"
              .format(os.cpu_count(), n_threads))
        print("[INFO]:\n --- Tile Extraction Progress Bar: ")
        for y in tqdm(range(1, Y_pixels, n_threads*patch_size_at_layer)):  # tqdm: lib for progress bar
            # Parallel speedup! multiple threads writing tiles at same time
            Parallel(n_jobs=n_threads, backend="threading")(
                delayed(tile_write_thread)
                (thread_y_dim, self.slide, slide_level_num, X_pixels, Y_pixels, self.patch_size, patch_size_at_layer, self.patch_saver)
                for thread_y_dim in range(y, y + n_threads*patch_size_at_layer, patch_size_at_layer)
            )
        print("Total Time cost: ", time.time() - start)


def tile_write_thread(y, slide, slide_level_num, X_pixels, Y_pixels, patch_size, patch_size_at_layer, tiles_saver):
    """ Thread function for writing tile image
    :arg
        -   y: y coord
        -   slide: slide object, extracted from OpenSlide
        -   slide_level_num: number of level in slide/SVS file
        -   X_pixels, Y_pixels: X Y dimension of a slide level
        -   patch_size: extract patch size; e.p. 100*100 for lymphocyte theano model)
    """
    # gather a line of tiles, then write them into database file. Avoid freq. file ops.
    if y < Y_pixels:  # QX 09/01/2020: don't go be-young the boundary!
        files = []  # list of tile image files
        for x in range(1, X_pixels, patch_size_at_layer):
            patch_filename = str(x)+'_'+str(y)+'_'+str(patch_size_at_layer)+'_'+str(patch_size)
            patch_img = slide.read_region((x, y), slide_level_num, (patch_size_at_layer, patch_size_at_layer))
            patch_img = patch_img.resize((patch_size, patch_size), Image.ANTIALIAS)
            patch_img = patch_img.convert('RGB')  # convert RGBA to RGB
            files.append([patch_filename, patch_img])
        # write batches to lmdb database
        tiles_saver.write_batch(batch=files)
        files.clear()  # free memory
