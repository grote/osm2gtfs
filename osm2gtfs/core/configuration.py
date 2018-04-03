# coding=utf-8

import os
import sys
import logging
import json
import datetime
from urllib2 import urlopen
from calendar import monthrange
from osm2gtfs.core.cache import Cache


class Configuration(object):
    """The Configuration class validates and prepares configuration data from
    the config file for further use in the script.

    """

    def __init__(self, args):
        """Contructor function

        This function gets called when Configuration object are created.

        Based on the configuration from the config file it validates and
        prepares all mandatory configuration elements.

        """
        # Load config file from argument of standard location
        self.data = self._load_config(args)

        # Define name for output file
        self.output = self._define_output_file(args)

        # Validate and prepare start and end date
        self._prepare_dates()

        # Initiate variable for schedule source information
        self._schedule_source = None

    def get_schedule_source(self, refresh=False):
        """Loads the schedule source information.

        Loads a schedule source file from either a path or a url specified
        in the config file

        :return schedule_source: The schedule read from a file.

        """

        if 'schedule_source' not in self.data:
            return None

        else:
            source_file = self.data['schedule_source']
            cached_file = self.data['selector'] + '-schedule'

            # Preferably return cached data about schedule
            if refresh is False:
                # Check if _schedule_source data is already present
                if not self._schedule_source:
                    # If not, try to get _schedule_source from file cache
                    self._schedule_source = Cache.read_file(cached_file)
                # Return cached data if found
                if bool(self._schedule_source):
                    return self._schedule_source

            # No cached data was found or refresh was forced
            logging.info("Load schedule source information from %s", source_file)

            # Check if local file exists
            if os.path.isfile(source_file):

                # Open file and add to config object
                with open(source_file, 'r') as f:
                    schedule_source = f.read()

            else:
                # Check if it is a valid url
                try:
                    schedule_source_file = urlopen(source_file)
                except ValueError:
                    logging.error("Couldn't find schedule_source file.")
                    sys.exit(0)
                schedule_source = schedule_source_file.read()

        self._schedule_source = schedule_source

        # Cache data
        Cache.write_file(cached_file, self._schedule_source)
        return self._schedule_source

    def _load_config(self, args):
        """Loads the configuration. Either the standard location
        (config.json) or a location specified as an command argument.

        :return config: A dictionary of configuration data.

        """
        # Load config json file
        if args.config is not None:
            config = Configuration.load_config_file(args.config)
        elif os.path.isfile('config.json'):
            with open("config.json") as json_file:
                config = Configuration.load_config_file(json_file)
        else:
            logging.error("No config.json file found.")
            sys.exit(0)

        return config

    @staticmethod
    def load_config_file(configfile):
        """
        Loads json from config file

        :return config: A dictionary of configuration data.

        """
        try:
            config = json.load(configfile)
        except ValueError, e:
            logging.error('Config json file is invalid.')
            logging.error(e)
            sys.exit(0)

        return config

    def _define_output_file(self, args):
        """
        Defines the filename for GTFS file to write.
        Either from config file or command argument.

        :return output: Filename for saving GTFS output file.

        """
        # Get and check filename for gtfs output
        if args.output is not None:
            output_file = args.output
        elif 'output_file' in self.data:
            output_file = self.data['output_file']
        else:
            logging.error('No filename for gtfs file specified.')
            sys.exit(0)

        return output_file

    def _prepare_dates(self):
        """
        Validate and prepare start and end date.
        Either from config file or based on current date.

        """
        config = self.data

        start_date = False
        if 'start_date' in config['feed_info']:
            try:
                start_date = datetime.datetime.strptime(
                    config['feed_info']['start_date'], "%Y%m%d")
            except ValueError, e:
                logging.warning('"start_date" from config file %s', e)

        if not start_date:
            # Use first of current month if no start date was specified
            now = datetime.datetime.now()
            start_date = datetime.datetime.strptime(
                now.strftime('%Y%m') + "01", "%Y%m%d")
            config['feed_info']['start_date'] = now.strftime('%Y%m') + "01"
            logging.info("Using the generated start date: %s", config['feed_info']['start_date'])

        end_date = False
        if 'end_date' in config['feed_info']:
            try:
                end_date = datetime.datetime.strptime(
                    config['feed_info']['end_date'], "%Y%m%d")
                logging.info("Using the end date from config file: %s",
                             config['feed_info']['end_date'])
            except ValueError, e:
                logging.warning('"end_date" from config file %s', e)

        if not end_date:

            # Define end date automatically one year from start date
            if start_date.month == 1:
                # Special case in January of each year
                end_date_month = "12"
                end_date_year = start_date.year
            else:
                # Regular case for all other months
                end_date_year = start_date.year + 1
                end_date_month = str(start_date.month - 1)
                if len(end_date_month) == 1:
                    end_date_month = "0" + end_date_month

            end_date_day = monthrange(end_date_year, int(end_date_month))[1]
            end_date = datetime.datetime(day=end_date_day,
                                         month=int(end_date_month),
                                         year=end_date_year)
            config['feed_info']['end_date'] = str(
                end_date.year) + end_date_month + str(end_date.day)
            logging.info("Using the generated end date: %s", config['feed_info']['end_date'])

        # Validate dates
        if start_date > end_date:
            logging.error('End dates finishes before start date.')
            sys.exit(0)
        elif end_date - start_date > datetime.timedelta(days=364):
            logging.warning("Date range is more than one year.")
