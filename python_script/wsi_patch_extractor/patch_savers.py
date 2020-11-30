import h5py
import lmdb
import pickle
import os, sys
from PIL import Image
from matplotlib import pyplot as plt


class LmdbSaver:
    def __init__(self, save_path, filename):
        # lmdb environment set
        self.env = lmdb.open(path=os.path.join(save_path, filename),
                             map_size=16*1024*1024*1024, map_async=True)  # try 16GB cache

    def write_batch(self, batch):
        """ Write a batch of extracted tile images to lmdb
        :args
            -   batch: tile image batch
        """
        with self.env.begin(write=True) as txn:  # txn: transaction obj of lmdb
            for i in range(len(batch)):
                txn.put(key=batch[i][0].encode('ascii'), value=pickle.dumps(batch[i][1], protocol=2))

    def write_meta(self, meta_info):
        """ Write tile meta info to lmdb file
        :args
            -   {meta}: meta dictionary: like tile dimension, patch size, total slide x,y size in pixel
        :MEMO
            -   pickle protocol version set as 2, for python 2.7 compatibility
                    : pickle.dumps(meta_info, protocol=2)
        """
        with self.env.begin(write=True) as txn:  # txn: transaction obj of lmdb
            txn.put(key='meta_info'.encode('ascii'), value=pickle.dumps(meta_info, protocol=2))


class Hdf5Saver:
    def __init__(self):
        self.saver = h5py.Saver()


# class PngSaver:
#    def __init__(self):
