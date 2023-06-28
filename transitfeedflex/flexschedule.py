from transitfeed.schedule import Schedule

class FlexSchedule(Schedule):

  def ConnectDb(self, memory_db):
    super(FlexSchedule, self).ConnectDb(memory_db)
    cursor = self._connection.cursor()
    cursor.execute("""ALTER TABLE stop_times ADD continuous_pickup INTEGER;""")
    cursor.execute("""ALTER TABLE stop_times ADD continuous_drop_off INTEGER;""")


