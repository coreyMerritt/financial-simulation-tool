from dataclasses import dataclass
from datetime import date
from models.enums.asset_type import AssetType
from models.enums.time_period_type import TimePeriodType


@dataclass
class AssetConfig:
  name: str
  type: AssetType
  value: float
  appreciation_rate: float
  appreciation_period_type: TimePeriodType
  appreciation_period_value: int
  pays_capital_gains_tax: bool
  sell_date: date | None
