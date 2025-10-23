from dataclasses import dataclass
from datetime import date


@dataclass
class OutputConfig:
  pause_on_output: bool
  every_day: bool
  every_week: bool
  every_month: bool
  every_year: bool
  every_decade: bool
  start_date: date | None
  end_date: date
