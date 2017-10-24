# coding=utf-8

import unittest
import os
import importlib
from osm2gtfs.core.configuration import Configuration


class TestCoreCreatorFactory(unittest.TestCase):

    def test_naming_convention(self):

        path = os.path.dirname(__file__) + "/../../creators/"
        creators = ['agency', 'feed_info', 'routes', 'schedule', 'stops', 'trips']

        # pylint: disable=unused-variable
        for subdir, dirs, files in os.walk(path):

            # Loop through available directories of creators
            for selector in dirs:

                # Check if creator directory fits naming convention
                self.assertTrue(
                    self._check_naming_convention(selector),
                    'The path "creators/' + selector +
                    ' " doesn\'t fit the naming convention.')

                # Check for existing configuration file
                config_file_path = path + selector + "/config.json"
                self.assertTrue(
                    os.path.isfile(config_file_path),
                    'No correctly named configuration file found for: ' +
                    selector)

                # Check whether selector in config file is correctly
                config = Configuration.load_config_file(open(config_file_path))
                self.assertEqual(
                    selector, config['selector'],
                    "The selector (" + config['selector'] +
                    ") in config file is not equal to the directory name: " +
                    selector)

                # Loop through available files in creator directories and check
                # whether they are correctly named
                for inner_subdir, inner_dirs, inner_files in os.walk(
                        path + selector):

                    for filename in inner_files:
                        # Check the Python files (and ignore the others)
                        if filename.endswith(
                                '.py') and not filename == "__init__.py":

                            # Check if selector has been properly applied to
                            # file name
                            self.assertTrue(
                                filename.endswith(selector + '.py'),
                                "This file is not well named: " + filename)

                            # Check for valid creators
                            split_filename = filename.split("_")
                            if split_filename[0] == "feed":
                                split_filename[0] = split_filename[0] + split_filename.pop(1)
                            self.assertTrue(
                                split_filename[0] in creators,
                                "This file is not well named: " + filename)
                            self.assertEqual(
                                split_filename[1], "creator",
                                "This file is not well named: " + filename)

                            # Try to import the content of the creator module
                            correct_class_name_state = True
                            try:
                                module = importlib.import_module(
                                    ".creators." + selector + "." + filename[:-3],
                                    package="osm2gtfs")
                            except ImportError:
                                correct_class_name_state = False

                            # Snake to camel case to test for correct class names
                            classname = ''.join(x.capitalize() for x in filename[:-3].split('_'))
                            try:
                                var = getattr(module, classname)
                            except AttributeError:
                                correct_class_name_state = False

                            self.assertTrue(correct_class_name_state,
                                            "The required class " + classname +
                                            " wasn't found in " + filename + " ")

    def _check_naming_convention(self, selector):
        check = True
        if "_" in selector:
            split_selector = selector.split("_")

            # Check for ISO 3166-2 country code
            if not len(split_selector[0]) == 2:
                check = False

            # Check for amount of split elements; can only be 2 or three
            if len(split_selector) < 2 or len(split_selector) > 3:
                check = False
        else:
            return False
        return check


def load_tests(loader, tests, pattern):
    # pylint: disable=unused-argument
    test_cases = ['test_naming_convention']
    suite = unittest.TestSuite(map(TestCoreCreatorFactory, test_cases))
    return suite


if __name__ == '__main__':
    unittest.main()
