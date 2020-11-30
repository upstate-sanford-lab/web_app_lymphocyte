"""
read tile images from LMDB file
testing purpose
"""
import os
import lmdb
import pickle
from PIL import Image


class LmdbReader:
    def __init__(self, path, name):
        # env, transaction(txn), cursor
        self.lmdb_env = lmdb.open(os.path.join(path, name))
        self.lmdb_txn = self.lmdb_env.begin()
        self.lmdb_cursor = self.lmdb_txn.cursor()

    def get_meta_info(self):
        meta = self.lmdb_txn.get('meta_info'.encode("ascii"))
        meta = pickle.loads(meta)
        # print("[INFO]:\n --- Tiles Meta Info", meta)
        return meta

    def get_sample_tile(self, tile_x, tile_y):
        """ Get a sample tile, for test
        :arg
            -   tile_x, tile_y: tile coordinate (x,y)
        """
        meta = self.get_tiles_meta()
        tile_size = meta['tile_size']
        tile_x_dim, tile_y_dim = meta['tile_x_dim'], meta['tile_y_dim']
        if tile_x < tile_x_dim and tile_y < tile_y_dim:
            pixel_x, pixel_y = tile_x * tile_size, tile_y * tile_size
            img = self.lmdb_txn.get((str(pixel_x)+'_'+str(pixel_y)).encode("ascii"))
            img = pickle.loads(img)
            img.show()
            print("Image size: ", img.size)
        else:
            print("tile num out of range! Please input within X:{0} | Y:{1}".format(tile_x_dim, tile_y_dim))

    def get_tile(self, tile_x, tile_y, tile_size):
        """ Get a tile, for test
        :arg
            -   tile_x, tile_y: tile coordinate (x,y)
            -   tile_size: pixel size of a tile; pixel_x = tile_x * tile_size
        """
        pixel_x, pixel_y = tile_x * tile_size, tile_y * tile_size
        img = self.lmdb_txn.get((str(pixel_x)+'_'+str(pixel_y)).encode("ascii"))
        img = pickle.loads(img)
        return img

