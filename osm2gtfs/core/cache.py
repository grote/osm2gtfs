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
        if not os.path.isdir('data'):
            os.mkdir('data')
        with open(os.path.join('data', name + '.pkl'), 'wb') as f:
            pickle.dump(content, f, pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def read_data(name):
        """Function to read cache

        Reads and returns an object (content) with an indicated name from a
        file on the hard drive.

        """
        filename = os.path.join('data', name + '.pkl')
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                content = pickle.load(f)
            return content
        else:
            return {}

    @staticmethod
    def write_file(name, content):
        """Function to write cache

        Writes an object (content) with an indicated name to a file on the
        hard drive.

        """
        if not os.path.isdir('data'):
            os.mkdir('data')
        with open(os.path.join('data', name), 'wb') as f:
            f.write(content)

    @staticmethod
    def read_file(name):
        """Function to read cache

        Reads and returns an object (content) with an indicated name from a
        file on the hard drive.

        :return file: The read file, or an empty dictionary in case no file
            was found
        """
        filename = os.path.join('data', name)
        if os.path.isfile(filename):
            with open(filename, 'rb') as f:
                return f.read()
        else:
            return dict()
