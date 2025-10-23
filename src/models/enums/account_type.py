from enum import Enum


class AccountType(Enum):
  CASH = "cash"
  SAVINGS = "savings"
  INVESTMENT = "investment"
  ROTH_IRA = "roth_ira"
  HSA = "hsa"
  FOURK = "fourk"
