#!/usr/bin/python2

from __future__ import absolute_import
import transitfeed

from . import flexstoptime

def GetGtfsFactory(factory = None):
  if not factory:
    factory = transitfeed.GetGtfsFactory()

  factory.UpdateClass('StopTime', flexstoptime.FlexStopTime)

  return factory
