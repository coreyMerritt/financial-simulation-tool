from dataclasses import dataclass
from datetime import date
from models.enums.time_period_type import TimePeriodType


@dataclass
class BillConfig:
  name: str
  charge: float
  charge_period_type: TimePeriodType
  charge_period_value: int
  annual_inflation_flat: float | None
  annual_inflation_percentage: float | None
  annual_inflation_period_type: TimePeriodType | None
  annual_inflation_period_value: int | None
  start_date: date
  end_date: date | None
