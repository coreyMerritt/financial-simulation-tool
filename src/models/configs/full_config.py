from dataclasses import dataclass
from datetime import date
from typing import List
from models.configs.account_config import AccountConfig
from models.configs.asset_config import AssetConfig
from models.configs.bill_config import BillConfig
from models.configs.debt_config import DebtConfig
from models.configs.income_stream_config import IncomeStreamConfig
from models.configs.output_config import OutputConfig


@dataclass
class FullConfig:
  married: bool | int
  payment_order: List[List]
  accounts: List[AccountConfig]
  bills: List[BillConfig]
  debts: List[DebtConfig]
  income: List[IncomeStreamConfig]
  assets: List[AssetConfig]
  dob: date
  output: OutputConfig
