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


