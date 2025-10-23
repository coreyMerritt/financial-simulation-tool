from dataclasses import dataclass
from datetime import date
from models.enums.account_type import AccountType
from models.enums.time_period_type import TimePeriodType


@dataclass
class AccountConfig:
  name: str
  type: AccountType
  balance: float
  interest_rate: float
  interest_period_type: TimePeriodType
  interest_period_value: int
  last_interest_date: date
  pays_capital_gains_tax: bool
  pays_income_tax: bool
