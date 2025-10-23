from datetime import date
from typing import List
from dateutil.relativedelta import relativedelta
from entities.account import Account
from entities.asset import Asset
from entities.external_entities.debtor import Debtor
from exceptions.bankrupt_exception import BankruptException
from models.configs.debt_config import DebtConfig
from models.enums.time_period_type import TimePeriodType
from services.financial_calculator import FinancialCalculator


class Debt:
  _name: str
  _principal: float
  _balance: float
  _start_date: date
  _end_date: date
  _interest_rate: float
  _interest_period_type: TimePeriodType
  _interest_period_value: int
  _last_interest_date: date
  _charge_period_type: TimePeriodType
  _charge_period_value: int
  _last_charge_date: date
  _asset: Asset | None

  def __init__(self, today: date, debt_config: DebtConfig):
    self._name = debt_config.name
    self._principal = debt_config.principal
    self._balance = debt_config.balance
    self._start_date = debt_config.start_date
    self._end_date = debt_config.end_date
    self._interest_rate = debt_config.interest_rate
    self._interest_period_type = debt_config.interest_period_type
    self._interest_period_value = debt_config.interest_period_value
    self.__init_last_interest_date(today, debt_config)
    self._charge_period_type = debt_config.charge_period_type
    self._charge_period_value = debt_config.charge_period_value
    self.__init_last_charge_date(today, debt_config)
    self._asset = None
    if debt_config.asset:
      self._asset = Asset(False, today, debt_config.asset)

  def __init_last_interest_date(self, today: date, debt_config: DebtConfig):
    if debt_config.interest_period_type == TimePeriodType.DAYS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(days=debt_config.interest_period_value)
    elif debt_config.interest_period_type == TimePeriodType.WEEKS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(weeks=debt_config.interest_period_value)
    elif debt_config.interest_period_type == TimePeriodType.MONTHS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(months=debt_config.interest_period_value)
    elif debt_config.interest_period_type == TimePeriodType.YEARS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(years=debt_config.interest_period_value)
    else:
      raise RuntimeError("Unknown interest_period_value")
    if debt_config.start_date >= OLDEST_HAPPY_LAST_INTEREST_DATE:
      self._last_interest_date = debt_config.start_date
    else:
      self._last_interest_date = OLDEST_HAPPY_LAST_INTEREST_DATE

  def __init_last_charge_date(self, today: date, debt_config: DebtConfig):
    if debt_config.charge_period_type == TimePeriodType.DAYS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(days=debt_config.charge_period_value)
    elif debt_config.charge_period_type == TimePeriodType.WEEKS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(weeks=debt_config.charge_period_value)
    elif debt_config.charge_period_type == TimePeriodType.MONTHS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(months=debt_config.charge_period_value)
    elif debt_config.charge_period_type == TimePeriodType.YEARS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(years=debt_config.charge_period_value)
    else:
      raise RuntimeError("Unknown charge_period_value")
    if debt_config.start_date >= OLDEST_HAPPY_LAST_CHARGE_DATE:
      self._last_charge_date = debt_config.start_date
    else:
      self._last_charge_date = OLDEST_HAPPY_LAST_CHARGE_DATE

  def is_interest_today(self, today: date) -> bool:
    if self._balance == 0:
      self._last_interest_date = today
      return False
    if today == self._start_date:
      return True
    if self._interest_period_type == TimePeriodType.DAYS:
      next_interest_day = self._last_interest_date + relativedelta(days=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.WEEKS:
      next_interest_day = self._last_interest_date + relativedelta(weeks=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.MONTHS:
      next_interest_day = self._last_interest_date + relativedelta(months=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.YEARS:
      next_interest_day = self._last_interest_date + relativedelta(years=self._interest_period_value)
    else:
      raise RuntimeError("Unknown interest_period_value")
    return today == next_interest_day

  def is_charge_today(self, today: date) -> bool:
    if self._balance == 0:
      self._last_charge_date = today
      return False
    if today == self._start_date:
      return True
    if self._charge_period_type == TimePeriodType.DAYS:
      next_charge_day = self._last_charge_date + relativedelta(days=self._charge_period_value)
    elif self._charge_period_type == TimePeriodType.WEEKS:
      next_charge_day = self._last_charge_date + relativedelta(weeks=self._charge_period_value)
    elif self._charge_period_type == TimePeriodType.MONTHS:
      next_charge_day = self._last_charge_date + relativedelta(months=self._charge_period_value)
    elif self._charge_period_type == TimePeriodType.YEARS:
      next_charge_day = self._last_charge_date + relativedelta(years=self._charge_period_value)
    else:
      raise RuntimeError("Unknown charge_period_value")
    return today == next_charge_day

  def get_name(self) -> str:
    return self._name

  def get_balance(self, today: date) -> float:
    if today < self._start_date:
      return 0.0
    return self._balance

  def get_interest_rate(self, today: date) -> float:
    if today < self._start_date:
      return 0.0
    return self._interest_rate

  def get_start_date(self) -> date:
    return self._start_date

  def get_end_date(self) -> date:
    return self._end_date

  def get_asset(self) -> Asset | None:
    return self._asset

  def pay(self, adjustment_amount: float) -> None:
    assert adjustment_amount <= self._balance
    self._balance -= adjustment_amount
    assert self._balance >= 0

  def print_balance(self, today: date) -> None:
    if self.get_balance(today) > 0:
      print(f"    {self._name} Balance: \033[38;2;255;128;0m${self.get_balance(today):,.2f}\033[0m")

  def handle_interest(self, today: date, is_print_day: bool) -> None:
    if not self.is_interest_today(today):
      return
    interest_gained = FinancialCalculator.get_interest(
      principal=self._balance,
      interest_rate=self._interest_rate,
      last_interest_date=self._last_interest_date,
      today=today
    )
    if interest_gained == 0:
      return
    if interest_gained < 0:
      raise RuntimeError(f"Debt gained below 0 interest: {interest_gained}")
    self._last_interest_date = today
    self._balance += interest_gained
    if is_print_day:
      print(f"  [Daily]   {self._name} Interest: \033[38;2;255;128;0m+${interest_gained:,.2f}\033[0m")

  def handle_charges(
    self,
    is_print_day: bool,
    today: date,
    age: relativedelta,
    accounts: List[Account],
    assets: List[Asset]
  ) -> None:
    if not self.is_charge_today(today):
      return
    if self.__is_last_charge():
      charge = self._balance
    else:
      charge = FinancialCalculator.get_minimum_monthly_payment(
        self._interest_rate,
        self._principal,
        self._start_date,
        self._end_date
      )
    if not self._last_charge_date:
      if today == self._start_date:
        self._last_charge_date = today
      elif today < self._start_date:
        return
      elif today > self._start_date:
        raise RuntimeError("No last_charge_date AND is later than start_date")
    total_balance = 0
    for account in accounts:
      total_balance += account.get_post_tax_balance(age)
    if total_balance < charge:
      raise BankruptException(charge)
    running_charge = charge
    assert running_charge <= self._balance + 0.01
    for account in accounts:
      account_balance = account.get_post_tax_balance(age)
      if account_balance > running_charge:
        running_charge_withdrawn = account.withdraw(running_charge, age)
        self.pay(running_charge_withdrawn)
        Debtor.give(running_charge_withdrawn)
        running_charge = 0
        break
      else:
        account_balance_withdrawn = account.withdraw(account_balance, age)
        self.pay(account_balance_withdrawn)
        Debtor.give(account_balance_withdrawn)
        running_charge -= account_balance_withdrawn
    self._last_charge_date = today
    if is_print_day:
      if self._charge_period_type == TimePeriodType.DAYS:
        print(f"  [Daily]   {self._name} Charge: \033[38;2;255;0;0m-${charge:,.2f}\033[0m")
      elif self._charge_period_type == TimePeriodType.WEEKS:
        print(f"  [Weekly]  {self._name} Charge: \033[38;2;255;0;0m-${charge:,.2f}\033[0m")
      elif self._charge_period_type == TimePeriodType.MONTHS:
        print(f"  [Monthly] {self._name} Charge: \033[38;2;255;0;0m-${charge:,.2f}\033[0m")
      elif self._charge_period_type == TimePeriodType.YEARS:
        print(f"  [Yearly]  {self._name} Charge: \033[38;2;255;0;0m-${charge:,.2f}\033[0m")
      else:
        raise RuntimeError("Unknown ChargePeriodType")
    if self._balance == 0:
      if self._asset:
        for asset in assets:
          if asset.get_name() == self._asset.get_name():
            asset.set_is_paid_off(True)
            break

  def __is_last_charge(self) -> bool:
    if self._charge_period_type == TimePeriodType.DAYS:
      next_charge_date = self._last_charge_date + relativedelta(days=self._charge_period_value)
    elif self._charge_period_type == TimePeriodType.WEEKS:
      next_charge_date = self._last_charge_date + relativedelta(weeks=self._charge_period_value)
    elif self._charge_period_type == TimePeriodType.MONTHS:
      next_charge_date = self._last_charge_date + relativedelta(months=self._charge_period_value)
    elif self._charge_period_type == TimePeriodType.YEARS:
      next_charge_date = self._last_charge_date + relativedelta(years=self._charge_period_value)
    else:
      raise RuntimeError("Unknown charge_period_type")
    if next_charge_date > self._end_date:
      return True
    minimum_monthly_payment = FinancialCalculator.get_minimum_monthly_payment(
      self._interest_rate,
      self._principal,
      self._start_date,
      self._end_date
    )
    if minimum_monthly_payment >= self._balance:
      return True
    return False
