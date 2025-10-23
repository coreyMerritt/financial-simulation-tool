from datetime import date
from typing import List
from dateutil.relativedelta import relativedelta
from entities.account import Account
from entities.external_entities.biller import Biller
from exceptions.bankrupt_exception import BankruptException
from models.configs.bill_config import BillConfig
from models.enums.time_period_type import TimePeriodType


class Bill():
  _name: str
  _charge: float
  _charge_period_type: TimePeriodType
  _charge_period_value: int
  _annual_inflation_flat: float | None
  _annual_inflation_percentage: float | None
  _annual_inflation_period_type: TimePeriodType | None
  _annual_inflation_period_value: int | None
  _last_increase_date: date | None
  _start_date: date
  _end_date: date | None
  _last_charge_date: date

  def __init__(self, today: date, bill_config: BillConfig):
    self._name = bill_config.name
    self._charge = bill_config.charge
    self._charge_period_type = bill_config.charge_period_type
    self._charge_period_value = bill_config.charge_period_value
    self._annual_inflation_flat = bill_config.annual_inflation_flat
    self._annual_inflation_percentage = bill_config.annual_inflation_percentage
    self._annual_inflation_period_type = bill_config.annual_inflation_period_type
    self._annual_inflation_period_value = bill_config.annual_inflation_period_value
    self.__init_last_increase_date(today, bill_config)
    self._start_date = bill_config.start_date
    self._end_date = bill_config.end_date
    if bill_config.start_date <= today:
      self._last_charge_date = bill_config.start_date
    self.__init_last_charge_date(today, bill_config)

  def __init_last_increase_date(self, today: date, bill_config: BillConfig):
    if not self._annual_inflation_period_type:
      self._last_increase_date = None
      return
    if not self._annual_inflation_period_value:
      self._last_increase_date = None
      return
    if bill_config.annual_inflation_period_type == TimePeriodType.DAYS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(days=self._annual_inflation_period_value)
    elif bill_config.annual_inflation_period_type == TimePeriodType.WEEKS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(weeks=self._annual_inflation_period_value)
    elif bill_config.annual_inflation_period_type == TimePeriodType.MONTHS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(months=self._annual_inflation_period_value)
    elif bill_config.annual_inflation_period_type == TimePeriodType.YEARS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(years=self._annual_inflation_period_value)
    else:
      raise RuntimeError("Unknown inflation_period_value")
    if bill_config.start_date >= OLDEST_HAPPY_LAST_INCREASE_DATE:
      self._last_increase_date = bill_config.start_date
    else:
      self._last_increase_date = OLDEST_HAPPY_LAST_INCREASE_DATE

  def __init_last_charge_date(self, today: date, bill_config: BillConfig):
    if bill_config.charge_period_type == TimePeriodType.DAYS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(days=bill_config.charge_period_value)
    elif bill_config.charge_period_type == TimePeriodType.WEEKS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(weeks=bill_config.charge_period_value)
    elif bill_config.charge_period_type == TimePeriodType.MONTHS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(months=bill_config.charge_period_value)
    elif bill_config.charge_period_type == TimePeriodType.YEARS:
      OLDEST_HAPPY_LAST_CHARGE_DATE = today - relativedelta(years=bill_config.charge_period_value)
    else:
      raise RuntimeError("Unknown charge_period_value")
    if bill_config.start_date >= OLDEST_HAPPY_LAST_CHARGE_DATE:
      self._last_charge_date = bill_config.start_date
    else:
      self._last_charge_date = OLDEST_HAPPY_LAST_CHARGE_DATE

  def increases_today(self, today: date) -> bool:
    if not self._annual_inflation_percentage and not self._annual_inflation_flat:
      return False
    if not self._annual_inflation_period_type:
      return False
    if not self._annual_inflation_period_value:
      return False
    if not self._last_increase_date:
      return False
    if self._annual_inflation_period_type == TimePeriodType.DAYS:
      next_increase_day = self._last_increase_date + relativedelta(days=self._annual_inflation_period_value)
    elif self._annual_inflation_period_type == TimePeriodType.WEEKS:
      next_increase_day = self._last_increase_date + relativedelta(weeks=self._annual_inflation_period_value)
    elif self._annual_inflation_period_type == TimePeriodType.MONTHS:
      next_increase_day = self._last_increase_date + relativedelta(months=self._annual_inflation_period_value)
    elif self._annual_inflation_period_type == TimePeriodType.YEARS:
      next_increase_day = self._last_increase_date + relativedelta(years=self._annual_inflation_period_value)
    else:
      raise RuntimeError("Unknown inflation_period_type")
    return today == next_increase_day

  def is_charge_today(self, today: date) -> bool:
    if self._charge == 0:
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

  def get_charge(self) -> float:
    return self._charge

  def get_end_date(self) -> date | None:
    return self._end_date

  def handle_potential_charge_increase(self, today: date, is_print_day: bool) -> None:
    if not self._annual_inflation_percentage and not self._annual_inflation_flat:
      return
    if not self._annual_inflation_period_type:
      return
    if not self._annual_inflation_period_value:
      return
    if not self.increases_today(today):
      return
    if self._annual_inflation_period_type == TimePeriodType.MONTHS:
      past_date = today - relativedelta(months=self._annual_inflation_period_value)
      days_elapsed = (today - past_date).days
    elif self._annual_inflation_period_type == TimePeriodType.YEARS:
      days_elapsed = self._annual_inflation_period_value * 365
    elif self._annual_inflation_period_type == TimePeriodType.WEEKS:
      days_elapsed = self._annual_inflation_period_value * 7
    elif self._annual_inflation_period_type == TimePeriodType.DAYS:
      days_elapsed = self._annual_inflation_period_value
    else:
      raise RuntimeError("Unknown inflation_period_type")
    if self._annual_inflation_percentage:
      daily_rate = (self._annual_inflation_percentage / 100) / 365
      daily_increase_dollar_amount = self._charge * daily_rate * days_elapsed
    elif self._annual_inflation_flat:
      daily_flat = self._annual_inflation_flat / 365
      daily_increase_dollar_amount = daily_flat * days_elapsed
    else:
      raise RuntimeError("Neither annual_inflation_percentage nor annual_inflation_flat was provided.")
    self._charge += daily_increase_dollar_amount
    self._last_increase_date = today
    if is_print_day:
      if self._annual_inflation_period_type == TimePeriodType.DAYS:
        print(f"  [Daily]   {self._name} increased by \033[38;2;255;0;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      elif self._annual_inflation_period_type == TimePeriodType.WEEKS:
        print(f"  [Weekly]  {self._name} increased by \033[38;2;255;0;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      elif self._annual_inflation_period_type == TimePeriodType.MONTHS:
        print(f"  [Monthly] {self._name} increased by \033[38;2;255;0;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      elif self._annual_inflation_period_type == TimePeriodType.YEARS:
        print(f"  [Yearly]  {self._name} increased by \033[38;2;255;0;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      else:
        raise RuntimeError("Unknown IncreasePeriodValue")

  def handle_potential_charge(
    self,
    is_print_day: bool,
    today: date,
    age: relativedelta,
    accounts: List[Account]
  ) -> None:
    if not self.is_charge_today(today):
      return
    if not self._last_charge_date:
      if today == self._start_date:
        self._last_charge_date = today
      else:
        return
    total_account_balances = 0
    for account in accounts:
      total_account_balances += account.get_post_tax_balance(age)
    if total_account_balances < self._charge:
      raise BankruptException(self._charge)
    running_charge = self._charge
    for account in accounts:
      account_balance = account.get_post_tax_balance(age)
      if account_balance > running_charge:
        Biller.give(account.withdraw(running_charge, age))
        running_charge = 0
        break
      else:
        Biller.give(account.withdraw(account_balance, age))
        running_charge -= account_balance
    self._last_charge_date = today
    if is_print_day:
      if self._charge_period_type == TimePeriodType.DAYS:
        print(f"  [Daily]   {self._name} Charge: \033[38;2;255;0;0m-${self._charge:,.2f}\033[0m")
      elif self._charge_period_type == TimePeriodType.WEEKS:
        print(f"  [Weekly]  {self._name} Charge: \033[38;2;255;0;0m-${self._charge:,.2f}\033[0m")
      elif self._charge_period_type == TimePeriodType.MONTHS:
        print(f"  [Monthly] {self._name} Charge: \033[38;2;255;0;0m-${self._charge:,.2f}\033[0m")
      elif self._charge_period_type == TimePeriodType.YEARS:
        print(f"  [Yearly]  {self._name} Charge: \033[38;2;255;0;0m-${self._charge:,.2f}\033[0m")
      else:
        raise RuntimeError("Unknown ChargePeriodType")
