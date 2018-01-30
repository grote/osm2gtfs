# coding=utf-8

import transitfeed


class FeedInfoCreator(object):

    def __init__(self, config):
        self.config = config.data

    def __repr__(self):
        rep = ""
        if self.config is not None:
            rep += str(self.config) + " | "
        return rep

    def add_feed_info_to_feed(self, feed):
        feed.AddFeedInfoObject(self.prepare_feed_info())

    def prepare_feed_info(self):
        """
        Loads feed info data from a json config file.
        Return a transitfeed.FeedInfo object
        """
        config = self.config
        feed_info = transitfeed.FeedInfo()
        feed_info.feed_publisher_name = config['feed_info']['publisher_name']
        feed_info.feed_publisher_url = config['feed_info']['publisher_url']
        feed_info.feed_lang = config['agency']['agency_lang']
        feed_info.feed_start_date = config['feed_info']['start_date']
        feed_info.feed_end_date = config['feed_info']['end_date']
        feed_info.feed_version = config['feed_info']['version']
        return feed_info
