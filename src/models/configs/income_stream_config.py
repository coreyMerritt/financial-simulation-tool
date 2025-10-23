from dataclasses import dataclass
from datetime import date
from models.enums.time_period_type import TimePeriodType


@dataclass
class IncomeStreamConfig:
  name: str
  gross: float
  health_insurance_premium: float
  annual_inflation_flat: float | None
  annual_inflation_percentage: float | None
  annual_inflation_period_type: TimePeriodType | None
  annual_inflation_period_value: int | None
  fourk: float
  fourk_employer_contribution: float
  hsa: float
  hsa_employer_contribution: float
  state_tax_percentage: float
  city_tax_percentage: float
  payment_period_type: TimePeriodType
  payment_period_value: int
  start_date: date
  end_date: date
