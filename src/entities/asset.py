from datetime import date
from dateutil.relativedelta import relativedelta
from models.configs.asset_config import AssetConfig
from models.enums.asset_type import AssetType
from models.enums.time_period_type import TimePeriodType
from services.financial_calculator import FinancialCalculator


class Asset:
  _name: str
  _type: AssetType
  _value: float
  _is_paid_off: bool
  _sold: bool
  _appreciation_rate: float
  _appreciation_period_type: TimePeriodType
  _appreciation_period_value: int
  _last_appreciation_date: date
  _pays_capital_gains_tax: bool
  _sell_date: date | None
  _currently_untaxed_gains: float

  def __init__(self, is_paid_off: bool, today: date, asset_config: AssetConfig):
    self._name = asset_config.name
    self._type = asset_config.type
    self._value = asset_config.value
    self._is_paid_off = is_paid_off
    self._sold = False
    self._appreciation_rate = asset_config.appreciation_rate
    self._appreciation_period_type = asset_config.appreciation_period_type
    self._appreciation_period_value = asset_config.appreciation_period_value
    self._last_appreciation_date = today
    self._pays_capital_gains_tax = asset_config.pays_capital_gains_tax
    self._sell_date = asset_config.sell_date
    self._currently_untaxed_gains = 0.0

  def __eq__(self, other):
    if not isinstance(other, Asset):
      return False
    return self._name == other._name

  def __hash__(self):
    return hash(self._name)

  def is_paid_off(self) -> bool:
    return self._is_paid_off

  def is_sold(self) -> bool:
    return self._sold

  def is_sellable(self) -> bool:
    if self._is_paid_off:
      if not self._sold:
        return True
    return False

  def appreciates_today(self, today: date) -> bool:
    assert not self._sold
    if self._value == 0:
      return False
    elif self._value < 0:
      raise RuntimeError("Asset value is below 0")
    if self._appreciation_period_type == TimePeriodType.DAYS:
      next_appreciation_day = self._last_appreciation_date + relativedelta(days=self._appreciation_period_value)
    elif self._appreciation_period_type == TimePeriodType.WEEKS:
      next_appreciation_day = self._last_appreciation_date + relativedelta(weeks=self._appreciation_period_value)
    elif self._appreciation_period_type == TimePeriodType.MONTHS:
      next_appreciation_day = self._last_appreciation_date + relativedelta(months=self._appreciation_period_value)
    elif self._appreciation_period_type == TimePeriodType.YEARS:
      next_appreciation_day = self._last_appreciation_date + relativedelta(years=self._appreciation_period_value)
    else:
      raise RuntimeError("Unknown appreciation_period_type")
    return today >= next_appreciation_day

  def get_post_tax_value(self) -> float:
    assert not self._sold
    capital_gains_tax = 0
    if self._pays_capital_gains_tax:
      taxable_gains = self._currently_untaxed_gains
      capital_gains_tax = taxable_gains * 0.15
    return self._value - capital_gains_tax

  def get_appreciation_rate(self) -> float:
    assert not self._sold
    return self._appreciation_rate

  def get_value(self) -> float:
    assert not self._sold
    return self._value

  def get_name(self) -> str:
    return self._name

  def get_sell_date(self) -> date | None:
    return self._sell_date

  def get_type(self) -> AssetType:
    assert not self._sold
    return self._type

  def set_is_paid_off(self, value: bool) -> None:
    assert not self._sold
    self._is_paid_off = value

  def sell(self) -> float:
    post_tax_value = self.get_post_tax_value()
    self._sold = True
    return post_tax_value

  def print_value(self) -> None:
    assert not self._sold
    print(f"    {self._name} Value: \033[38;2;91;91;255m${self.get_value():,.2f}\033[0m")

  def print_post_tax_value(self) -> None:
    assert not self._sold
    print(f"    {self._name} Post-Tax Value: \033[38;2;91;91;255m${self.get_post_tax_value():,.2f}\033[0m")

  def handle_appreciation(self, today: date, is_print_day: bool) -> None:
    assert not self._sold
    if not self.appreciates_today(today):
      return
    interest_gained = FinancialCalculator.get_interest(
      principal=self._value,
      interest_rate=self._appreciation_rate,
      last_interest_date=self._last_appreciation_date,
      today=today
    )
    if interest_gained == 0:
      return
    self._last_appreciation_date = today
    self._value += interest_gained
    if is_print_day:
      if interest_gained > 0:
        print(f"  [Daily]   {self._name} Appreciation: \033[38;2;0;255;0m+${interest_gained:,.2f}\033[0m")
      else:
        print(f"  [Daily]   {self._name} Depreciation: \033[38;2;255;0;0m-${abs(interest_gained):,.2f}\033[0m")
