from transitfeed.trip import Trip

import transitfeed.problems as problems_module

class FlexTrip(Trip):
  def GetStopTimes(self, problems=None):
    """Adds continuous_pickup + continuous_drop_off to fetching script"""
    # In theory problems=None should be safe because data from database has been
    # validated. See comment in _LoadStopTimes for why this isn't always true.
    cursor = self._schedule._connection.cursor()
    cursor.execute(
        'SELECT arrival_secs,departure_secs,stop_headsign,pickup_type,'
        'drop_off_type,shape_dist_traveled,stop_id,stop_sequence,timepoint, continuous_pickup, continuous_drop_off '
        'FROM stop_times '
        'WHERE trip_id=? '
        'ORDER BY stop_sequence', (self.trip_id,))
    stop_times = []
    stoptime_class = self.GetGtfsFactory().StopTime
    if problems is None:
      # TODO: delete this branch when StopTime.__init__ doesn't need a
      # ProblemReporter
      problems = problems_module.default_problem_reporter
    for row in cursor.fetchall():
      stop = self._schedule.GetStop(row[6])
      stop_times.append(stoptime_class(problems=problems,
                                       stop=stop,
                                       arrival_secs=row[0],
                                       departure_secs=row[1],
                                       stop_headsign=row[2],
                                       pickup_type=row[3],
                                       drop_off_type=row[4],
                                       shape_dist_traveled=row[5],
                                       stop_sequence=row[7],
                                       timepoint=row[8],
                                       continuous_pickup=row[9],
                                       continuous_drop_off=row[10]))
    return stop_times
