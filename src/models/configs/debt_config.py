from dataclasses import dataclass
from datetime import date
from models.configs.asset_config import AssetConfig
from models.enums.time_period_type import TimePeriodType


@dataclass
class DebtConfig:
  name: str
  principal: float
  balance: float
  start_date: date
  end_date: date
  interest_rate: float
  interest_period_type: TimePeriodType
  interest_period_value: int
  charge_period_type: TimePeriodType
  charge_period_value: int
  asset: AssetConfig | None
