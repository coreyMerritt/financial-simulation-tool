from datetime import date
from typing import List
from dateutil.relativedelta import relativedelta
from entities.account import Account
from entities.debt import Debt
from entities.external_entities.city_government import CityGovernment
from entities.external_entities.debtor import Debtor
from entities.external_entities.department_of_social_security import DepartmentOfSocialSecurity
from entities.external_entities.employer import Employer
from entities.external_entities.internal_revenue_service import InternalRevenueService
from entities.external_entities.healthcare_provider import HealthcareProvider
from entities.external_entities.state_government import StateGovernment
from entities.external_entities.us_treasury import UsTreasury
from entities.misc.annual_federal_income_tax_record import AnnualFederalIncomeTaxRecord
from models.configs.income_stream_config import IncomeStreamConfig
from models.enums.account_type import AccountType
from models.enums.time_period_type import TimePeriodType
from services.financial_calculator import FinancialCalculator


class IncomeStream:
  _name: str
  _annual_gross_income: float
  _period_health_insurance_premium: float
  _annual_inflation_flat: float | None
  _annual_inflation_percentage: float | None
  _annual_inflation_period_type: TimePeriodType | None
  _annual_inflation_period_value: int | None
  _annual_fourk_contribution: float
  _annual_fourk_employer_contribution: float
  _annual_hsa_contribution: float
  _annual_hsa_employer_contribution: float
  _state_tax_percentage: float
  _city_tax_percentage: float
  _payment_period_type: TimePeriodType
  _payment_period_value: int
  _start_date: date
  _end_date: date
  _last_payment_date: date
  _last_increase_date: date | None

  def __init__(self, today: date, income_config: IncomeStreamConfig):
    self._name = income_config.name
    self._annual_gross_income = income_config.gross
    self._period_health_insurance_premium = income_config.health_insurance_premium
    self._annual_inflation_flat = income_config.annual_inflation_flat
    self._annual_inflation_percentage = income_config.annual_inflation_percentage
    self._annual_inflation_period_type = income_config.annual_inflation_period_type
    self._annual_inflation_period_value = income_config.annual_inflation_period_value
    self._annual_fourk_contribution = income_config.fourk
    self._annual_fourk_employer_contribution = income_config.fourk_employer_contribution
    self._annual_hsa_contribution = income_config.hsa
    self._annual_hsa_employer_contribution = income_config.hsa_employer_contribution
    self._state_tax_percentage = income_config.state_tax_percentage
    self._city_tax_percentage = income_config.city_tax_percentage
    self._payment_period_type = income_config.payment_period_type
    self._payment_period_value = income_config.payment_period_value
    start_date = income_config.start_date
    self._start_date = start_date
    self.__init_last_payment_date(today, income_config)
    self.__init_last_increase_date(today, income_config)
    self._end_date = income_config.end_date

  def __init_last_payment_date(self, today: date, income_config: IncomeStreamConfig):
    if income_config.payment_period_type == TimePeriodType.DAYS:
      OLDEST_HAPPY_LAST_PAYMENT_DATE = today - relativedelta(days=income_config.payment_period_value)
    elif income_config.payment_period_type == TimePeriodType.WEEKS:
      OLDEST_HAPPY_LAST_PAYMENT_DATE = today - relativedelta(weeks=income_config.payment_period_value)
    elif income_config.payment_period_type == TimePeriodType.MONTHS:
      OLDEST_HAPPY_LAST_PAYMENT_DATE = today - relativedelta(months=income_config.payment_period_value)
    elif income_config.payment_period_type == TimePeriodType.YEARS:
      OLDEST_HAPPY_LAST_PAYMENT_DATE = today - relativedelta(years=income_config.payment_period_value)
    else:
      raise RuntimeError("Unknown payment_period_value")
    if income_config.start_date >= OLDEST_HAPPY_LAST_PAYMENT_DATE:
      self._last_payment_date = income_config.start_date
    else:
      self._last_payment_date = OLDEST_HAPPY_LAST_PAYMENT_DATE

  def __init_last_increase_date(self, today: date, income_config: IncomeStreamConfig):
    if not self._annual_inflation_period_type:
      self._last_increase_date = None
      return
    if not self._annual_inflation_period_value:
      self._last_increase_date = None
      return
    if income_config.annual_inflation_period_type == TimePeriodType.DAYS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(days=self._annual_inflation_period_value)
    elif income_config.annual_inflation_period_type == TimePeriodType.WEEKS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(weeks=self._annual_inflation_period_value)
    elif income_config.annual_inflation_period_type == TimePeriodType.MONTHS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(months=self._annual_inflation_period_value)
    elif income_config.annual_inflation_period_type == TimePeriodType.YEARS:
      OLDEST_HAPPY_LAST_INCREASE_DATE = today - relativedelta(years=self._annual_inflation_period_value)
    else:
      raise RuntimeError("Unknown inflation_period_value")
    if income_config.start_date >= OLDEST_HAPPY_LAST_INCREASE_DATE:
      self._last_increase_date = income_config.start_date
    else:
      self._last_increase_date = OLDEST_HAPPY_LAST_INCREASE_DATE

  def is_payment_today(self, today: date) -> bool:
    if self._annual_gross_income == 0:
      return False
    if today == self._start_date:
      return True
    if self._payment_period_type == TimePeriodType.DAYS:
      next_payment_day = self._last_payment_date + relativedelta(days=self._payment_period_value)
    elif self._payment_period_type == TimePeriodType.WEEKS:
      next_payment_day = self._last_payment_date + relativedelta(weeks=self._payment_period_value)
    elif self._payment_period_type == TimePeriodType.MONTHS:
      next_payment_day = self._last_payment_date + relativedelta(months=self._payment_period_value)
    elif self._payment_period_type == TimePeriodType.YEARS:
      next_payment_day = self._last_payment_date + relativedelta(years=self._payment_period_value)
    else:
      raise RuntimeError("Unknown payment_period_value")
    return today == next_payment_day

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

  def get_annual_gross_income(self) -> float:
    return self._annual_gross_income

  def get_end_date(self) -> date:
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
      daily_increase_dollar_amount = self._annual_gross_income * daily_rate * days_elapsed
    elif self._annual_inflation_flat:
      daily_flat = self._annual_inflation_flat / 365
      daily_increase_dollar_amount = daily_flat * days_elapsed
    else:
      raise RuntimeError("Neither annual_inflation_percentage nor annual_inflation_flat was provided.")
    self._annual_gross_income += daily_increase_dollar_amount
    self._last_increase_date = today
    if is_print_day:
      if self._annual_inflation_period_type == TimePeriodType.DAYS:
        print(f"  [Daily]   {self._name} increased by \033[38;2;0;255;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      elif self._annual_inflation_period_type == TimePeriodType.WEEKS:
        print(f"  [Weekly]  {self._name} increased by \033[38;2;0;255;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      elif self._annual_inflation_period_type == TimePeriodType.MONTHS:
        print(f"  [Monthly] {self._name} increased by \033[38;2;0;255;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      elif self._annual_inflation_period_type == TimePeriodType.YEARS:
        print(f"  [Yearly]  {self._name} increased by \033[38;2;0;255;0m+${daily_increase_dollar_amount:,.2f}\033[0m")
      else:
        raise RuntimeError("Unknown IncreasePeriodValue")

  def handle_potential_payout(
    self,
    is_print_day: bool,
    is_married: bool,
    today: date,
    annual_federal_income_tax_record: AnnualFederalIncomeTaxRecord,
    payment_order: List[List],
    accounts: List[Account],
    debts: List[Debt]
  ) -> None:
    if today > self._end_date:
      return
    if today < self._start_date:
      return
    if not self.is_payment_today(today):
      return
    net_payout = None
    time_since_last_payment = today - self._last_payment_date
    if self._payment_period_type == TimePeriodType.DAYS:
      payment_period_in_days = self._payment_period_value
    elif self._payment_period_type == TimePeriodType.WEEKS:
      payment_period_in_days = self._payment_period_value * 7
    elif self._payment_period_type == TimePeriodType.MONTHS:
      payment_period_in_days = (today - self._last_payment_date).days
    elif self._payment_period_type == TimePeriodType.YEARS:
      payment_period_in_days = self._payment_period_value * 365
    else:
      raise RuntimeError("Unknown payment_period_type")
    if time_since_last_payment.days >= payment_period_in_days:
      net_payout = self.__get_period_net_payout(
        is_print_day,
        is_married,
        today,
        annual_federal_income_tax_record,
        accounts
      )
    if net_payout:
      if is_print_day:
        print(f"  {self._name} Payout: \033[38;2;0;255;0m+${net_payout:,.2f}\033[0m")
      self.__pay_accounts(accounts, net_payout, payment_order, debts, today, is_print_day)
    self._last_payment_date = today

  def __pay_accounts(
    self,
    accounts: List[Account],
    payout: float,
    payment_order: List[List],
    debts: List[Debt],
    today: date,
    is_print_day: bool
  ) -> None:
    rollover = payout
    sorted_debts = sorted(debts, key=lambda d: d.get_interest_rate(today), reverse=True)
    for potential_account in payment_order:
      account_name = str(potential_account[0])
      if account_name.lower() == "debt":
        pay_interest_above = potential_account[1]
        for debt in sorted_debts:
          if rollover == 0:
            break
          if debt.get_interest_rate(today) < pay_interest_above:
            continue
          balance = debt.get_balance(today)
          if balance > 0:
            if is_print_day:
              print(f"    {debt.get_name()}: \033[38;2;0;255;0m-${rollover:,.2f}\033[0m")
            if balance > rollover:
              debt.pay(rollover)
              Debtor.give(rollover)
              rollover = 0
            else:
              debt.pay(balance)
              Debtor.give(balance)
              rollover -= balance
              assert rollover > 0
      else:
        account_goal = potential_account[1]
        account_found = False
        for account in accounts:
          if rollover == 0:
            break
          if account.get_name() == account_name:
            account_found = True
            if not account_goal or account.get_balance() < account_goal:
              if is_print_day:
                print(f"    {account.get_name()}: \033[38;2;0;255;0m+${rollover:,.2f}\033[0m")
              account.deposit(rollover)
              rollover = 0
              break
        assert account_found
      if rollover == 0:
        break

  def __get_period_net_payout(
    self,
    is_print_day: bool,
    is_married: bool,
    today: date,
    annual_federal_income_tax_record: AnnualFederalIncomeTaxRecord,
    accounts: List[Account]
  ) -> float:
    if self._payment_period_type == TimePeriodType.DAYS:
      payment_period_in_days = self._payment_period_value
    elif self._payment_period_type == TimePeriodType.WEEKS:
      payment_period_in_days = self._payment_period_value * 7
    elif self._payment_period_type == TimePeriodType.MONTHS:
      payment_period_in_days = (today - self._last_payment_date).days
    elif self._payment_period_type == TimePeriodType.YEARS:
      payment_period_in_days = self._payment_period_value * 365
    else:
      raise RuntimeError("Unknown payment_period_type")
    # Gross
    pay_period_gross = self._annual_gross_income / (365 / payment_period_in_days)
    annual_federal_income_tax_record.add_income(pay_period_gross)
    pay_period_net = Employer.take(pay_period_gross)
    # Health Insurance Premium
    pay_period_health_insurance_premium = self._period_health_insurance_premium
    pay_period_net -= pay_period_health_insurance_premium
    HealthcareProvider.give(pay_period_health_insurance_premium)
    # 401k
    pay_period_fourk_contribution = self._annual_fourk_contribution / (365 / payment_period_in_days)
    pay_period_net -= pay_period_fourk_contribution
    self.__deposit_to_first_fourk(is_print_day, pay_period_fourk_contribution, accounts)
    pay_period_fourk_employer_contribution = self._annual_fourk_employer_contribution / (365 / payment_period_in_days)
    Employer.take(pay_period_fourk_employer_contribution)
    self.__deposit_to_first_fourk(is_print_day, pay_period_fourk_employer_contribution, accounts)
    # HSA
    pay_period_hsa_contribution = self._annual_hsa_contribution / (365 / payment_period_in_days)
    pay_period_net -= pay_period_hsa_contribution
    self.__deposit_to_first_hsa(is_print_day, pay_period_hsa_contribution, accounts)
    pay_period_hsa_employer_contribution = self._annual_hsa_employer_contribution / (365 / payment_period_in_days)
    pay_period_net -= pay_period_hsa_employer_contribution
    self.__deposit_to_first_hsa(is_print_day, pay_period_hsa_employer_contribution, accounts)
    # Federal Tax
    annual_federal_tax = FinancialCalculator.calculate_federal_tax(is_married, self._annual_gross_income)
    pay_period_federal_tax = annual_federal_tax / (365 / payment_period_in_days)
    pay_period_net -= pay_period_federal_tax
    InternalRevenueService.give(pay_period_federal_tax)
    annual_federal_income_tax_record.add_tax_paid(pay_period_federal_tax)
    # State Tax
    pay_period_state_tax = pay_period_gross * (self._state_tax_percentage / 100)
    pay_period_net -= pay_period_state_tax
    StateGovernment.give(pay_period_state_tax)
    # City Tax
    pay_period_city_tax = pay_period_gross * (self._city_tax_percentage / 100)
    pay_period_net -= pay_period_city_tax
    CityGovernment.give(pay_period_city_tax)
    # Social Security
    annual_social_security = self._annual_gross_income * 0.062
    if annual_social_security > 10453.2:
      pay_period_social_security = 10453.2 / (365 / payment_period_in_days)
    else:
      pay_period_social_security = annual_social_security / (365 / payment_period_in_days)
    pay_period_net -= pay_period_social_security
    DepartmentOfSocialSecurity.give(pay_period_social_security)
    # Medicare
    if self._annual_gross_income > 200000:
      pay_period_medicare_tax = ((self._annual_gross_income - 200000) * 0.009) / (365 / payment_period_in_days)
    else:
      pay_period_medicare_tax = (self._annual_gross_income * 0.0145) / (365 / payment_period_in_days)
    pay_period_net -= pay_period_medicare_tax
    UsTreasury.give(pay_period_medicare_tax)
    return pay_period_net

  def __deposit_to_first_fourk(self, is_print_day: bool, payout: float, accounts: List[Account]) -> None:
    for account in accounts:
      if account.get_type() == AccountType.FOURK:  # We just deposit into the first HSA we find. Can do better
        account.deposit(payout)
        break
    if is_print_day:
      print(f"  {self._name} 401k Payout: \033[38;2;0;255;0m+${payout:,.2f}\033[0m")

  def __deposit_to_first_hsa(self, is_print_day: bool, payout: float, accounts: List[Account]) -> None:
    for account in accounts:
      if account.get_type() == AccountType.HSA:  # We just deposit into the first HSA we find. Can do better
        account.deposit(payout)
        break
    if is_print_day:
      print(f"  {self._name} HSA Payout: \033[38;2;0;255;0m+${payout:,.2f}\033[0m")
