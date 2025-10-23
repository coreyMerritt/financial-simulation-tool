from datetime import date
from dateutil.relativedelta import relativedelta
from entities.external_entities.bank import Bank
from entities.external_entities.internal_revenue_service import InternalRevenueService
from entities.external_entities.stock_market import StockMarket
from models.configs.account_config import AccountConfig
from models.enums.account_type import AccountType
from models.enums.time_period_type import TimePeriodType
from services.financial_calculator import FinancialCalculator


class Account:
  _account_types_that_gain_interest = [
    AccountType.SAVINGS
  ]
  _account_types_that_accrue_capital_gains = [
    AccountType.FOURK,
    AccountType.HSA,
    AccountType.INVESTMENT,
    AccountType.ROTH_IRA
  ]
  _name: str
  _type: AccountType
  _balance: float
  _interest_rate: float
  _interest_period_type: TimePeriodType
  _interest_period_value: int
  _last_interest_date: date
  _pays_capital_gains_tax: bool
  _pays_income_tax: bool
  _currently_untaxed_gains: float

  def __init__(self, today: date, account_config: AccountConfig):
    self._name = account_config.name
    self._type = account_config.type
    self._balance = account_config.balance
    self._interest_rate = account_config.interest_rate
    self._interest_period_type = account_config.interest_period_type
    self._interest_period_value = account_config.interest_period_value
    self.__init_last_interest_date(today, account_config)
    self._pays_capital_gains_tax = account_config.pays_capital_gains_tax
    self._pays_income_tax = account_config.pays_income_tax
    self._currently_untaxed_gains = 0.0

  def __init_last_interest_date(self, today: date, account_config: AccountConfig):
    if account_config.interest_period_type == TimePeriodType.DAYS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(days=account_config.interest_period_value)
    elif account_config.interest_period_type == TimePeriodType.WEEKS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(weeks=account_config.interest_period_value)
    elif account_config.interest_period_type == TimePeriodType.MONTHS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(months=account_config.interest_period_value)
    elif account_config.interest_period_type == TimePeriodType.YEARS:
      OLDEST_HAPPY_LAST_INTEREST_DATE = today - relativedelta(years=account_config.interest_period_value)
    else:
      raise RuntimeError("Unknown interest_period_type")
    if account_config.last_interest_date >= OLDEST_HAPPY_LAST_INTEREST_DATE:
      self._last_interest_date = account_config.last_interest_date
    else:
      self._last_interest_date = OLDEST_HAPPY_LAST_INTEREST_DATE

  def is_interest_today(self, today: date) -> bool:
    if not self._interest_rate:
      return False
    if not self._interest_period_type:
      return False
    if not self._interest_period_value:
      return False
    if not self._last_interest_date:
      return False
    if self._balance == 0:
      self._last_interest_date = today
      return False
    if self._type not in self._account_types_that_gain_interest:
      return False
    if self._interest_period_type == TimePeriodType.DAYS:
      next_interest_day = self._last_interest_date + relativedelta(days=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.WEEKS:
      next_interest_day = self._last_interest_date + relativedelta(weeks=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.MONTHS:
      next_interest_day = self._last_interest_date + relativedelta(months=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.YEARS:
      next_interest_day = self._last_interest_date + relativedelta(years=self._interest_period_value)
    else:
      raise RuntimeError("Unknown interest_period_type")
    return today == next_interest_day

  def is_capital_gains_today(self, today: date) -> bool:
    if not self._interest_rate:
      return False
    if not self._interest_period_type:
      return False
    if not self._interest_period_value:
      return False
    if not self._last_interest_date:
      return False
    if self._balance == 0:
      self._last_interest_date = today
      return False
    if not self._type in self._account_types_that_accrue_capital_gains:
      return False
    if self._interest_period_type == TimePeriodType.DAYS:
      next_interest_day = self._last_interest_date + relativedelta(days=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.WEEKS:
      next_interest_day = self._last_interest_date + relativedelta(weeks=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.MONTHS:
      next_interest_day = self._last_interest_date + relativedelta(months=self._interest_period_value)
    elif self._interest_period_type == TimePeriodType.YEARS:
      next_interest_day = self._last_interest_date + relativedelta(years=self._interest_period_value)
    else:
      raise RuntimeError("Unknown interest_period_type")
    return today == next_interest_day

  def get_name(self) -> str:
    return self._name

  def get_balance(self) -> float:
    return self._balance

  def get_interest_rate(self) -> float:
    return self._interest_rate

  def get_type(self) -> AccountType:
    return self._type

  def get_post_tax_balance(self, age: relativedelta) -> float:
    capital_gains_tax = 0
    income_tax = 0
    penalty = 0
    account_type = self.get_type()
    if self._pays_capital_gains_tax:
      taxable_gains = self._currently_untaxed_gains
      capital_gains_tax = taxable_gains * 0.15
    if self._pays_income_tax:
      income_tax = self._balance * 0.22
    AGE_IN_MONTHS = age.years * 12 + age.months
    FOURK_AGE_IN_MONTHS = 59 * 12 + 6
    IS_BELOW_FOURK_AGE = AGE_IN_MONTHS < FOURK_AGE_IN_MONTHS
    if IS_BELOW_FOURK_AGE:
      if account_type == AccountType.FOURK or account_type == AccountType.ROTH_IRA:
        penalty = self._balance * 0.1
    HSA_AGE_IN_MONTHS = 65 * 12
    IS_BELOW_HSA_AGE = AGE_IN_MONTHS < HSA_AGE_IN_MONTHS
    if IS_BELOW_HSA_AGE:
      if account_type == AccountType.HSA:
        penalty = self._balance * 0.2
    return self._balance - (capital_gains_tax + income_tax + penalty)

  def withdraw(self, asking_amount: float, age: relativedelta) -> float:
    capital_gains_tax = 0
    income_tax = 0
    penalty = 0
    account_type = self.get_type()
    if self._pays_capital_gains_tax:
      taxable_gains = min(asking_amount, self._currently_untaxed_gains)
      capital_gains_tax = taxable_gains * 0.15
    if self._pays_income_tax:
      income_tax = asking_amount * 0.22
    AGE_IN_MONTHS = age.years * 12 + age.months
    FOURK_AGE_IN_MONTHS = 59 * 12 + 6
    IS_BELOW_FOURK_AGE = AGE_IN_MONTHS < FOURK_AGE_IN_MONTHS
    if IS_BELOW_FOURK_AGE:
      if account_type == AccountType.FOURK or account_type == AccountType.ROTH_IRA:
        penalty = asking_amount * 0.1
        input(f"\n\033[38;2;255;0;0mWARNING:\033[0m Withdrawing from \033[38;2;255;0;0m{self.get_name()}\033[0m before age of 59.5")  # pylint: disable=line-too-long
    HSA_AGE_IN_MONTHS = 65 * 12
    IS_BELOW_HSA_AGE = AGE_IN_MONTHS < HSA_AGE_IN_MONTHS
    if IS_BELOW_HSA_AGE:
      if account_type == AccountType.HSA:
        penalty = asking_amount * 0.2
        input(f"\n\033[38;2;255;0;0mWARNING:\033[0m Withdrawing from \033[38;2;255;0;0m{self.get_name()}\033[0m before age of 65")  # pylint: disable=line-too-long
    assert self._balance >= asking_amount + capital_gains_tax + income_tax + penalty
    self._currently_untaxed_gains -= capital_gains_tax
    assert self._currently_untaxed_gains >= 0
    amount_to_withdraw_with_tax = (asking_amount + capital_gains_tax + income_tax + penalty)
    self._balance -= amount_to_withdraw_with_tax
    InternalRevenueService.give(capital_gains_tax)
    InternalRevenueService.give(income_tax)
    InternalRevenueService.give(penalty)
    return asking_amount

  def deposit(self, adjustment_amount) -> None:
    self._balance += adjustment_amount

  def print_balance(self) -> None:
    print(f"    {self._name} Balance: \033[38;2;0;255;0m${self.get_balance():,.2f}\033[0m")

  def handle_interest(self, today: date, is_print_day: bool) -> None:
    if not self.is_interest_today(today):
      return
    assert self._type in self._account_types_that_gain_interest
    assert self._interest_rate
    assert self._interest_period_type
    assert self._interest_period_value
    assert self._last_interest_date
    interest_gained = FinancialCalculator.get_interest(
      principal=self._balance,
      interest_rate=self._interest_rate,
      last_interest_date=self._last_interest_date,
      today=today
    )
    if interest_gained == 0:
      return
    if interest_gained < 0:
      raise RuntimeError(f"Account gained below 0 interest: {interest_gained}")
    self._last_interest_date = today
    self._balance += Bank.take(interest_gained)
    if is_print_day:
      print(f"  [Daily]   {self._name} Interest: \033[38;2;0;255;0m+${interest_gained:,.2f}\033[0m")

  def handle_capital_gains(self, today: date, is_print_day: bool) -> None:
    if not self.is_capital_gains_today(today):
      return
    assert self._type in self._account_types_that_accrue_capital_gains
    assert self._interest_rate
    assert self._interest_period_type
    assert self._interest_period_value
    assert self._last_interest_date
    capital_gains = FinancialCalculator.get_interest(
      principal=self._balance,
      interest_rate=self._interest_rate,
      last_interest_date=self._last_interest_date,
      today=today
    )
    if capital_gains == 0:
      return
    if capital_gains < 0:
      raise RuntimeError(f"Account gained below 0 interest: {capital_gains}")
    self._last_interest_date = today
    if self._type == AccountType.FOURK:
      self._balance += StockMarket.take(capital_gains)
    elif self._type == AccountType.HSA:
      self._balance += StockMarket.take(capital_gains)
    elif self._type == AccountType.INVESTMENT:
      self._balance += StockMarket.take(capital_gains)
    elif self._type == AccountType.ROTH_IRA:
      self._balance += StockMarket.take(capital_gains)
    else:
      raise RuntimeError("Unknown AccountType")
    if is_print_day:
      print(f"  [Daily]   {self._name} Capital Gains: \033[38;2;0;255;0m+${capital_gains:,.2f}\033[0m")
