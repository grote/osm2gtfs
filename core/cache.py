# coding=utf-8

import os
import pickle


class Cache(object):
    """The Cache class retrieves or writes data to a file cache on the hard
    drive.

    """

    @staticmethod
    def write_data(name, content):
        """Function to write cache

        Writes an object (content) with an indicated name to a file on the
        hard drive.

        """
        if not  os.path.isdir('data'): #checking is the dir exist
                os.mkdir('data')
        with open('data/' + name + '.pkl', 'wb') as f:
            pickle.dump(content, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def read_data(name):
        """Function to read cache

        Reads and returns an object (content) with an indicated name from a
        file on the hard drive.

        """
        if os.path.isfile('data/' + name + '.pkl'):
            with open('data/' + name + '.pkl', 'rb') as f:
                content = pickle.load(f)
            return content
        else:
            return {}
