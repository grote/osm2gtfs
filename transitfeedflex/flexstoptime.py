from transitfeed.stoptime import StopTime

class FlexStopTime(StopTime):

  _OPTIONAL_FIELD_NAMES = StopTime._OPTIONAL_FIELD_NAMES + [ 'continuous_pickup', 'continuous_drop_off']

  _FIELD_NAMES = StopTime._REQUIRED_FIELD_NAMES + _OPTIONAL_FIELD_NAMES

  _SQL_FIELD_NAMES = StopTime._SQL_FIELD_NAMES + [ 'continuous_pickup', 'continuous_drop_off']
  
  __slots__ = StopTime.__slots__ + ('continuous_pickup_flag', 'continuous_drop_off_flag')

  def __init__(self, problems, stop, arrival_time=None, departure_time=None, stop_headsign=None, pickup_type=None, drop_off_type=None, shape_dist_traveled=None, arrival_secs=None, departure_secs=None, stop_time=None, stop_sequence=None, timepoint=None, continuous_pickup=None, continuous_drop_off=None):
    super(FlexStopTime, self).__init__(problems, stop, arrival_time=arrival_time, departure_time=departure_time, stop_headsign=stop_headsign, pickup_type=pickup_type, drop_off_type=drop_off_type, shape_dist_traveled=shape_dist_traveled, arrival_secs=arrival_secs, departure_secs=departure_secs, stop_time=stop_time, stop_sequence=stop_sequence, timepoint=timepoint)
    self.continuous_pickup_flag = continuous_pickup
    self.continuous_drop_off_flag = continuous_drop_off

  def __getattr__(self, name):
    if name == 'continuous_pickup':
      if self.continuous_drop_off_flag == None:
        return ''
      return str(self.continuous_pickup_flag) # force 0 to be exported, because default = 1 = blank
    elif name == 'continuous_drop_off':
      if self.continuous_drop_off_flag == None:
         return ''
      return str(self.continuous_drop_off_flag)
    return super(FlexStopTime, self).__getattr__(name)

  def GetFieldValuesTuple(self, trip_id):
    result = []
    for fn in self._FIELD_NAMES:
      if fn == "trip_id":
        result.append(trip_id)
      else:
        # Since we'll be writting to an output file, we want empty values to be
        # outputted as an empty string
        # for timepoint, 1 is default, so 0 needs to be printed as string!
        if fn == 'timepoint':
          if self.timepoint == None:
            result.append('')
          else:
            result.append(str(self.timepoint))
        else:
          result.append(getattr(self, fn) or "")
    return tuple(result)


