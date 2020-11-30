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

    def get_tiles_meta(self):
        meta = self.lmdb_txn.get('tiles_meta'.encode("ascii"))
        meta = pickle.loads(meta)
        print("[INFO]:\n --- Tiles Meta Info", meta)
        return meta

    def get_sample_tile(self, pixel_x, pixel_y):
        """ Get a sample tile, for test
        :arg
            -   tile_x, tile_y: tile coordinate (x,y)
        """
        img = self.lmdb_txn.get((str(pixel_x)+'_'+str(pixel_y)+'_203_100').encode("ascii"))
        img = pickle.loads(img)
        print("image mode:{} size:{}".format(img.mode, img.size))
        img.show()

    def get_tile(self, pixel_x, pixel_y):
        """ Get a tile, for test
        :arg
            -   tile_x, tile_y: tile coordinate (x,y)
            -   tile_size: pixel size of a tile; pixel_x = tile_x * tile_size
        """
        img = self.lmdb_txn.get((str(pixel_x)+'_'+str(pixel_y)+'_203_100').encode("ascii"))
        img = pickle.loads(img)
        return img

    def print_keys(self):
        keys = []
        for key, _ in self.lmdb_cursor:
            print(key)
            keys.append(str(key))
        print(sorted(keys))

