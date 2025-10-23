#!/usr/bin/env python3
from datetime import date
import sys
from typing import List
from dateutil.relativedelta import relativedelta
import yaml
from entities.account import Account
from entities.accounting_record import AccountingRecord
from entities.asset import Asset
from entities.bill import Bill
from entities.debt import Debt
from entities.external_entities.bank import Bank
from entities.external_entities.biller import Biller
from entities.external_entities.buyer import Buyer
from entities.external_entities.city_government import CityGovernment
from entities.external_entities.debtor import Debtor
from entities.external_entities.department_of_social_security import DepartmentOfSocialSecurity
from entities.external_entities.employer import Employer
from entities.external_entities.internal_revenue_service import InternalRevenueService
from entities.external_entities.healthcare_provider import HealthcareProvider
from entities.external_entities.state_government import StateGovernment
from entities.external_entities.stock_market import StockMarket
from entities.external_entities.us_treasury import UsTreasury
from entities.income import IncomeStream
from entities.misc.annual_federal_income_tax_record import AnnualFederalIncomeTaxRecord
from exceptions.bankrupt_exception import BankruptException
from exceptions.unknown_account_type_exception import UnknownAccountTypeException
from exceptions.unknown_asset_type_exception import UnknownAssetTypeException
from exceptions.unknown_time_period_type_exception import UnknownTimePeriodTypeException
from models.configs.account_config import AccountConfig
from models.configs.asset_config import AssetConfig
from models.configs.bill_config import BillConfig
from models.configs.debt_config import DebtConfig
from models.configs.full_config import FullConfig
from models.configs.income_stream_config import IncomeStreamConfig
from models.configs.output_config import OutputConfig
from models.enums.account_type import AccountType
from models.enums.asset_type import AssetType
from models.enums.time_period_type import TimePeriodType


def main():
  today = date.today()
  full_config = __build_full_config("./config/prod/main.yml")
  assert isinstance(full_config, FullConfig)
  married = full_config.married
  if isinstance(married, bool):
    year_married = today.year
    is_married = married
  elif isinstance(married, int):
    year_married = married
    if today.year >= year_married:
      is_married = True
    else:
      is_married = False
  else:
    raise RuntimeError("Bad value for \"married\"")
  DATE_OF_BIRTH = full_config.dob
  accounts = __build_accounts(today, full_config.accounts)
  bills = __build_starting_bills(today, full_config.bills)
  debts = __build_starting_debts(today, full_config.debts)
  income_streams = __build_starting_incomes(today, full_config.income)
  assets = __build_all_assets(today, full_config.assets)
  last_output_date = today
  STARTING_ACCOUNTING_RECORD = __build_accounting_record(accounts)
  STARTING_CIRCULATION = STARTING_ACCOUNTING_RECORD.get_current_circulation()
  current_years_annual_federal_tax_income_record = AnnualFederalIncomeTaxRecord()
  last_years_annual_federal_tax_income_record = AnnualFederalIncomeTaxRecord()
  try:
    while today <= full_config.output.end_date:
      CURRENT_ACCOUNTING_RECORD = __build_accounting_record(accounts)
      CURRENT_CIRCULATION = CURRENT_ACCOUNTING_RECORD.get_current_circulation()
      assert abs(STARTING_CIRCULATION - CURRENT_CIRCULATION) < 0.01
      age = relativedelta(today, DATE_OF_BIRTH)
      __check_for_new_bills(today, full_config.bills, bills)
      __check_for_new_debts(today, full_config.debts, debts)
      __check_for_new_incomes(today, full_config.income, income_streams)
      __check_for_new_assets(assets, debts, today)
      __check_asset_sell_dates(today, accounts, assets)
      assets = [a for a in assets if not a.is_sold()]
      __check_for_ended_bills(today, bills)
      __check_for_ended_debts(today, debts)
      __check_for_ended_incomes(today, income_streams)
      IS_PRINT_DAY = __is_print_day(full_config, today, last_output_date)
      if IS_PRINT_DAY:
        last_output_date = today
        __print_new_day_header(today, age)
        __print_header("Today's Actions")
      IS_SHUFFLE_DAY = __is_income_payment(income_streams, today)
      __handle_todays_income(
        IS_PRINT_DAY,
        is_married,
        today,
        current_years_annual_federal_tax_income_record,
        accounts,
        debts,
        income_streams,
        full_config.payment_order
      )
      __handle_todays_appreciation(IS_PRINT_DAY, today, assets)
      __handle_todays_interest(IS_PRINT_DAY, today, accounts, debts)
      __handle_todays_capital_gains(IS_PRINT_DAY, today, accounts)
      __handle_todays_inflation_adjustments(IS_PRINT_DAY, today, bills, income_streams)
      __handle_todays_payments(IS_PRINT_DAY, today, age, accounts, assets, bills, debts)
      IS_NEW_YEAR = today.month == 1 and today.day == 1
      if IS_NEW_YEAR:
        last_years_annual_federal_tax_income_record = current_years_annual_federal_tax_income_record
        current_years_annual_federal_tax_income_record = AnnualFederalIncomeTaxRecord()
        if not is_married and (year_married + 1) == today.year:
          is_married = True
      IS_TAX_DAY = today.month == 4 and today.day == 15
      if IS_TAX_DAY:
        __handle_tax_day(IS_PRINT_DAY, is_married, age, last_years_annual_federal_tax_income_record, accounts)
      if IS_SHUFFLE_DAY:
        __shuffle_funds(age, full_config.payment_order, accounts)
      if IS_PRINT_DAY:
        __print_summary(today, debts, accounts, assets)
      if IS_PRINT_DAY and full_config.output.pause_on_output:
        print(f"\n\t[{__get_formatted_date(today)} --- Age: {age.years}]")
        input("\nPress enter to continue...\n")
      today += relativedelta(days=1)
    taken_from_employers = STARTING_ACCOUNTING_RECORD.employer - CURRENT_ACCOUNTING_RECORD.employer
    print(f"{"Obtained from employers":>26} (Includes taxes and fees): {f'${taken_from_employers:,.2f}':>14}")
    taken_from_stock_market = STARTING_ACCOUNTING_RECORD.stock_market - CURRENT_ACCOUNTING_RECORD.stock_market
    print(f"{"Obtained from stock market":>26} (Includes taxes and fees): {f'${taken_from_stock_market:,.2f}':>14}\n")
  except BankruptException as b:
    __print_new_day_header(today, age)
    __print_summary(today, debts, accounts, assets)
    print(f"\nUnable to pay: \033[38;2;255;0;0m${b.get_money_needed():,.2f}\n\tBankrupt\n\033[0m")
    sys.exit(0)

def __handle_todays_income(
  is_print_day: bool,
  is_married: bool,
  today: date,
  annual_federal_income_tax_record: AnnualFederalIncomeTaxRecord,
  accounts: List[Account],
  debts: List[Debt],
  income_streams: List[IncomeStream],
  payment_order: List[List]
) -> None:
  IS_INCOME_PRINT_DAY = is_print_day and __is_income_payment(income_streams, today)
  if IS_INCOME_PRINT_DAY:
    print("IncomeStream Payments:")
  for income in income_streams:
    income.handle_potential_payout(
      is_print_day,
      is_married,
      today,
      annual_federal_income_tax_record,
      payment_order,
      accounts,
      debts
    )
  if IS_INCOME_PRINT_DAY:
    print()

def __handle_todays_appreciation(
  is_print_day: bool,
  today: date,
  assets: List[Asset]
) -> None:
  IS_APPRECIATION_PRINT_DAY = is_print_day and __is_asset_appreciation(assets, today)
  if IS_APPRECIATION_PRINT_DAY:
    print("Asset Appreciation:")
  for asset in assets:
    asset.handle_appreciation(today, is_print_day)
  if IS_APPRECIATION_PRINT_DAY:
    print()

def __handle_todays_interest(
  is_print_day: bool,
  today: date,
  accounts: List[Account],
  debts: List[Debt]
) -> None:
  IS_ACCOUNT_INTEREST_PRINT_DAY = is_print_day and __is_account_interest(accounts, today)
  IS_DEBT_INTEREST_PRINT_DAY = is_print_day and __is_debt_interest(debts, today)
  if IS_ACCOUNT_INTEREST_PRINT_DAY:
    print("Account Interest:")
  for account in accounts:
    account.handle_interest(today, is_print_day)
  if IS_ACCOUNT_INTEREST_PRINT_DAY:
    print()
  if IS_DEBT_INTEREST_PRINT_DAY:
    print("Debt Interest:")
  for debt in debts:
    debt.handle_interest(today, is_print_day)
  if IS_DEBT_INTEREST_PRINT_DAY:
    print()

def __handle_todays_capital_gains(
  is_print_day: bool,
  today: date,
  accounts: List[Account]
) -> None:
  IS_ACCOUNT_CAPITAL_GAINS_PRINT_DAY = is_print_day and __is_capital_gains(accounts, today)
  if IS_ACCOUNT_CAPITAL_GAINS_PRINT_DAY:
    print("Capital Gains:")
  for account in accounts:
    account.handle_capital_gains(today, is_print_day)
  if IS_ACCOUNT_CAPITAL_GAINS_PRINT_DAY:
    print()

def __handle_todays_inflation_adjustments(
  is_print_day: bool,
  today: date,
  bills: List[Bill],
  incomes: List[IncomeStream]
):
  IS_BILL_INFLATION_ADJUSTMENT_PRINT_DAY = is_print_day and __is_bill_charge_increase(bills, today)
  if IS_BILL_INFLATION_ADJUSTMENT_PRINT_DAY:
    print("Inflation Adjustments:")
  for bill in bills:
    bill.handle_potential_charge_increase(today, is_print_day)
  IS_INCOME_INFLATION_ADJUSTMENT_PRINT_DAY = is_print_day and __is_income_charge_increase(incomes, today)
  for income in incomes:
    income.handle_potential_charge_increase(today, is_print_day)
  if IS_BILL_INFLATION_ADJUSTMENT_PRINT_DAY or IS_INCOME_INFLATION_ADJUSTMENT_PRINT_DAY:
    print()

def __handle_todays_payments(
  is_print_day: bool,
  today: date,
  age: relativedelta,
  accounts: List[Account],
  assets: List[Asset],
  bills: List[Bill],
  debts: List[Debt]
) -> None:
  IS_BILL_PAYMENT_PRINT_DAY = is_print_day and __is_bill_charge(bills, today)
  IS_DEBT_PAYMENT_PRINT_DAY = is_print_day and __is_debt_charge(debts, today)
  if IS_BILL_PAYMENT_PRINT_DAY:
    print("Bill Payments:")
  for bill in bills:
    try:
      bill.handle_potential_charge(is_print_day, today, age, accounts)
    except BankruptException as e:
      if __get_total_available_funds(age, accounts, assets) < e.get_money_needed():
        raise e
      __sell_appropriate_assets(e.get_money_needed(), assets, accounts)
      assets = [a for a in assets if not a.is_sold()]
      bill.handle_potential_charge(is_print_day, today, age, accounts)
  if IS_BILL_PAYMENT_PRINT_DAY:
    print()
  if IS_DEBT_PAYMENT_PRINT_DAY:
    print("Debt Payments:")
  for debt in debts:
    try:
      debt.handle_charges(is_print_day, today, age, accounts, assets)
    except BankruptException as e:
      if __get_total_available_funds(age, accounts, assets) < e.get_money_needed():
        raise e
      __sell_appropriate_assets(e.get_money_needed(), assets, accounts)
      assets = [a for a in assets if not a.is_sold()]
      debt.handle_charges(is_print_day, today, age, accounts, assets)
  if IS_DEBT_PAYMENT_PRINT_DAY:
    print()

def __build_full_config(yaml_path: str) -> FullConfig:
  with open(yaml_path, "r", encoding="utf-8") as raw_config:
    yaml_config = yaml.safe_load(raw_config)
  dob = __build_date(yaml_config["dob"])
  assert dob
  full_config = FullConfig(
    married=yaml_config["married"],
    payment_order=yaml_config["payment_order"],
    accounts=__build_accounts_configs(yaml_config["accounts"]),
    bills=__build_bills_configs(yaml_config["bills"]),
    debts=__build_debts_configs(yaml_config["debts"]),
    income=__build_income_configs(yaml_config["income"]),
    assets=__build_asset_configs(yaml_config["assets"]),
    dob=dob,
    output=__build_output_config(yaml_config["output"])
  )
  return full_config

def __build_output_config(output_dict: dict) -> OutputConfig:
  start_date = __build_date(output_dict["start_date"])
  end_date = __build_date(output_dict["end_date"])
  assert end_date
  output_config = OutputConfig(
    pause_on_output=output_dict["pause_on_output"],
    every_day=output_dict["every_day"],
    every_week=output_dict["every_week"],
    every_month=output_dict["every_month"],
    every_year=output_dict["every_year"],
    every_decade=output_dict["every_decade"],
    start_date=start_date,
    end_date=end_date
  )
  return output_config

def __build_accounts_configs(accounts_list: List[dict]) -> List[AccountConfig]:
  account_configs: List[AccountConfig] = []
  for account in accounts_list:
    account_type = __build_account_type(account["type"])
    interest_period_type = __build_time_period_type(account["interest_period_type"])
    assert interest_period_type
    last_interest_date = __build_date(account["last_interest_date"])
    assert last_interest_date
    account_configs.append(AccountConfig(
      name=account["name"],
      type=account_type,
      balance=account["balance"],
      interest_rate=account["interest_rate"],
      interest_period_type=interest_period_type,
      interest_period_value=account["interest_period_value"],
      last_interest_date=last_interest_date,
      pays_capital_gains_tax=account["pays_capital_gains_tax"],
      pays_income_tax=account["pays_income_tax"]
    ))
  return account_configs

def __build_debts_configs(debts_list: List[dict]) -> List[DebtConfig]:
  debt_configs: List[DebtConfig] = []
  for debt in debts_list:
    interest_period_type = __build_time_period_type(debt["interest_period_type"])
    assert interest_period_type
    charge_period_type = __build_time_period_type(debt["charge_period_type"])
    assert charge_period_type
    start_date = __build_date(debt["start_date"])
    assert start_date
    end_date = __build_date(debt["end_date"])
    assert end_date
    asset = None
    if debt["asset"]:
      asset = __build_asset_configs([debt["asset"]])[0]
    debt_configs.append(DebtConfig(
      name=debt["name"],
      principal=debt["principal"],
      balance=debt["balance"],
      start_date=start_date,
      end_date=end_date,
      interest_rate=debt["interest_rate"],
      interest_period_type=interest_period_type,
      interest_period_value=debt["interest_period_value"],
      charge_period_type=charge_period_type,
      charge_period_value=debt["charge_period_value"],
      asset=asset
    ))
  return debt_configs

def __build_income_configs(incomes_list: List[dict]) -> List[IncomeStreamConfig]:
  income_configs: List[IncomeStreamConfig] = []
  for income in incomes_list:
    payment_period_type = __build_time_period_type(income["payment_period_type"])
    assert payment_period_type
    annual_inflation_period_type = __build_time_period_type(income["annual_inflation_period_type"])
    assert annual_inflation_period_type
    start_date = __build_date(income["start_date"])
    assert start_date
    end_date = __build_date(income["end_date"])
    assert end_date
    income_configs.append(IncomeStreamConfig(
      name=income["name"],
      gross=income["gross"],
      health_insurance_premium=income["health_insurance_premium"],
      annual_inflation_flat=income["annual_inflation_flat"],
      annual_inflation_percentage=income["annual_inflation_percentage"],
      annual_inflation_period_type=annual_inflation_period_type,
      annual_inflation_period_value=income["annual_inflation_period_value"],
      fourk=income["401k"],
      fourk_employer_contribution=income["401k_employer_contribution"],
      hsa=income["hsa"],
      hsa_employer_contribution=income["hsa_employer_contribution"],
      state_tax_percentage=income["state_tax_percentage"],
      city_tax_percentage=income["city_tax_percentage"],
      payment_period_type=payment_period_type,
      payment_period_value=income["payment_period_value"],
      start_date=start_date,
      end_date=end_date
    ))
  return income_configs

def __build_asset_configs(assets_list: List[dict]) -> List[AssetConfig]:
  asset_configs: List[AssetConfig] = []
  for asset in assets_list:
    asset_type = __build_asset_type(asset["type"])
    assert asset_type
    return_period_type = __build_time_period_type(asset["appreciation_period_type"])
    assert return_period_type
    sell_date = __build_date(asset["sell_date"])
    asset_configs.append(AssetConfig(
      name=asset["name"],
      type=asset_type,
      value=asset["value"],
      appreciation_rate=asset["appreciation_rate"],
      appreciation_period_type=return_period_type,
      appreciation_period_value=asset["appreciation_period_value"],
      pays_capital_gains_tax=asset["pays_capital_gains_tax"],
      sell_date=sell_date
    ))
  return asset_configs

def __build_bills_configs(bills_list: List[dict]) -> List[BillConfig]:
  bill_configs: List[BillConfig] = []
  for bill in bills_list:
    charge_period_type = __build_time_period_type(bill["charge_period_type"])
    assert charge_period_type
    annual_inflation_period_type = __build_time_period_type(bill["annual_inflation_period_type"])
    assert annual_inflation_period_type
    start_date = __build_date(bill["start_date"])
    assert start_date
    end_date = __build_date(bill["end_date"])
    bill_configs.append(BillConfig(
      name=bill["name"],
      charge=bill["charge"],
      charge_period_type=charge_period_type,
      charge_period_value=bill["charge_period_value"],
      annual_inflation_flat=bill["annual_inflation_flat"],
      annual_inflation_percentage=bill["annual_inflation_percentage"],
      annual_inflation_period_type=annual_inflation_period_type,
      annual_inflation_period_value=bill["annual_inflation_period_value"],
      start_date=start_date,
      end_date=end_date
    ))
  return bill_configs

def __build_account_type(account_type_str: str) -> AccountType:
  if account_type_str.lower() == AccountType.CASH.value:
    interest_period_type = AccountType.CASH
  elif account_type_str.lower() == AccountType.SAVINGS.value:
    interest_period_type = AccountType.SAVINGS
  elif account_type_str.lower() == AccountType.INVESTMENT.value:
    interest_period_type = AccountType.INVESTMENT
  elif account_type_str.lower() == AccountType.ROTH_IRA.value:
    interest_period_type = AccountType.ROTH_IRA
  elif account_type_str.lower() == AccountType.HSA.value:
    interest_period_type = AccountType.HSA
  elif account_type_str.lower() == AccountType.FOURK.value:
    interest_period_type = AccountType.FOURK
  else:
    raise UnknownAccountTypeException(f"Given AccountType: {account_type_str}")
  return interest_period_type

def __build_time_period_type(time_period_type_str: str | None) -> TimePeriodType | None:
  if time_period_type_str is None:
    return None
  if time_period_type_str.lower() == TimePeriodType.DAYS.value:
    interest_period_type = TimePeriodType.DAYS
  elif time_period_type_str.lower() == TimePeriodType.WEEKS.value:
    interest_period_type = TimePeriodType.WEEKS
  elif time_period_type_str.lower() == TimePeriodType.MONTHS.value:
    interest_period_type = TimePeriodType.MONTHS
  elif time_period_type_str.lower() == TimePeriodType.YEARS.value:
    interest_period_type = TimePeriodType.YEARS
  else:
    raise UnknownTimePeriodTypeException(f"Given TimePeriodType: {time_period_type_str}")
  return interest_period_type

def __build_asset_type(asset_type_str: str | None) -> AssetType | None:
  if asset_type_str is None:
    return None
  if asset_type_str.lower() == AssetType.HOUSE.value:
    asset_type = AssetType.HOUSE
  elif asset_type_str.lower() == AssetType.CAR.value:
    asset_type = AssetType.CAR
  elif asset_type_str.lower() == AssetType.MISC.value:
    asset_type = AssetType.MISC
  else:
    raise UnknownAssetTypeException(f"Given AssetType: {asset_type_str}")
  return asset_type

def __build_date(date_dict: dict | None) -> date | None:
  if date_dict is None:
    return None
  return date(
    month=date_dict["month"],
    day=date_dict["day"],
    year=date_dict["year"]
  )

def __build_accounts(
  today: date,
  account_configs: List[AccountConfig]
) -> List[Account]:
  accounts: List[Account] = []
  for config in account_configs:
    accounts.append(Account(
      today=today,
      account_config=config
    ))
  return accounts

def __build_starting_bills(today: date, bills_configs: List[BillConfig]) -> List[Bill]:
  bills: List[Bill] = []
  for config in bills_configs:
    if today >= config.start_date:
      bills.append(Bill(
        today=today,
        bill_config=config
      ))
  return bills

def __build_starting_debts(today: date, debts_configs: List[DebtConfig]) -> List[Debt]:
  debts: List[Debt] = []
  for config in debts_configs:
    if today >= config.start_date:
      debts.append(Debt(
        today=today,
        debt_config=config
      ))
  return debts

def __build_starting_incomes(today: date, incomes_configs: List[IncomeStreamConfig]) -> List[IncomeStream]:
  incomes: List[IncomeStream] = []
  for config in incomes_configs:
    if today >= config.start_date:
      incomes.append(IncomeStream(
        today=today,
        income_config=config
      ))
  return incomes

def __build_all_assets(today: date, assets_configs: List[AssetConfig]) -> List[Asset]:
  assets: List[Asset] = []
  for config in assets_configs:
    assets.append(Asset(
      True,
      today,
      config
    ))
  return assets

def __check_for_new_bills(today: date, bills_configs: List[BillConfig], bills: List[Bill]) -> None:
  for config in bills_configs:
    if config.start_date == today:
      bills.append(Bill(today=today, bill_config=config))

def __check_for_new_debts(today: date, debts_configs: List[DebtConfig], debts: List[Debt]) -> None:
  for config in debts_configs:
    if config.start_date == today:
      debts.append(Debt(today=today, debt_config=config))

def __check_for_new_incomes(
  today: date,
  incomes_configs: List[IncomeStreamConfig],
  incomes: List[IncomeStream]
) -> None:
  for config in incomes_configs:
    if config.start_date == today:
      incomes.append(IncomeStream(today=today, income_config=config))

def __check_for_new_assets(assets: List[Asset], debts: List[Debt], today: date) -> None:
  for debt in debts:
    if today >= debt.get_start_date():
      debt_asset = debt.get_asset()
      if debt_asset:
        if debt_asset not in assets:
          assets.append(debt_asset)

def __check_asset_sell_dates(today: date, accounts: List[Account], assets: List[Asset]) -> None:
  for asset in assets:
    sell_date = asset.get_sell_date()
    if sell_date:
      if sell_date == today:
        if asset.is_sellable():
          for account in accounts:
            if account.get_type() == AccountType.INVESTMENT:
              sold_assets_worth = asset.sell()
              worth_taken_from_buyer = Buyer.take(sold_assets_worth)
              account.deposit(worth_taken_from_buyer)
              break

def __check_for_ended_bills(today: date, bills: List[Bill]) -> None:
  for bill in bills:
    end_date = bill.get_end_date()
    if end_date:
      if today > end_date:
        bills.remove(bill)

def __check_for_ended_debts(today: date, debts: List[Debt]) -> None:
  for debt in debts:
    if today > debt.get_end_date():
      debts.remove(debt)

def __check_for_ended_incomes(today: date, incomes: List[IncomeStream]) -> None:
  for income in incomes:
    if today > income.get_end_date():
      incomes.remove(income)

def __is_print_day(
  full_config: FullConfig,
  today: date,
  last_output_date: date
) -> bool:
  if full_config.output.start_date and today < full_config.output.start_date:
    return False
  if today > full_config.output.end_date:
    sys.exit(0)   # TODO: This really shouldn't just be dropped in here
  if today == full_config.output.start_date:
    return True
  if today == full_config.output.end_date:
    return True
  if full_config.output.every_day:
    return True
  elif full_config.output.every_week:
    return (today - last_output_date).days >= 7
  elif full_config.output.every_month:
    diff = relativedelta(today, last_output_date)
    return diff.months >= 1 or diff.years >= 1
  elif full_config.output.every_year:
    diff = relativedelta(today, last_output_date)
    return diff.years >= 1
  elif full_config.output.every_decade:
    diff = relativedelta(today, last_output_date)
    return diff.years >= 10
  return False

def __print_new_day_header(some_date: date, age: relativedelta) -> None:
  formatted_date = __get_formatted_date(some_date)
  print()
  print("─" * 120)
  print("─" * 120)
  print("─" * 120)
  print()
  print(f"\t{formatted_date}")
  print(f"\tAge:  {age.years}")

def __get_formatted_date(some_date: date) -> str:
  day = some_date.day
  suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
  formatted_date = some_date.strftime(f"Date: %A - %B {day}{suffix} %Y")
  return formatted_date

def __print_header(header: str) -> None:
  print(" " * 50)
  print("=" * 50)
  print(f"{header:^50}")
  print("=" * 50)
  print(" " * 50)

def __print_summary(today: date, debts: List[Debt], accounts: List[Account], assets: List[Asset]) -> None:
  __print_header("End of Day Summary")
  # Debts
  print("Debt Balances:")
  total_debt_balance = 0
  for debt in debts:
    total_debt_balance += debt.get_balance(today)
  print(f"  Total Debts Balance: \033[38;2;255;128;0m${total_debt_balance:,.2f}\033[0m")
  for debt in debts:
    debt.print_balance(today)
  # Accounts
  print("\nAccount Balances:")
  total_account_balance = 0
  for account in accounts:
    total_account_balance += account.get_balance()
  print(f"  Total Accounts Balance: \033[38;2;0;255;0m${total_account_balance:,.2f}\033[0m")
  for account in accounts:
    account.print_balance()
  # Assets
  print("\nAssets:")
  total_sellable_assets_value = 0
  for asset in assets:
    if asset.is_sellable():
      total_sellable_assets_value += asset.get_post_tax_value()
  print(f"  Total Sellable Assets Value: \033[38;2;91;91;255m${total_sellable_assets_value:,.2f}\033[0m")
  total_assets_value = 0
  for asset in assets:
    total_assets_value += asset.get_post_tax_value()
  print(f"  Total Unconditional Assets Value: \033[38;2;91;91;255m${total_assets_value:,.2f}\033[0m")
  for asset in assets:
    asset.print_value()
    if asset.is_paid_off():
      print("      Paid off: \033[38;2;0;255;0m✔\033[0m")
    else:
      print("      Paid off: \033[38;2;255;0;0m✘\033[0m")
  # Net Worth
  net_worth = total_account_balance + total_assets_value - total_debt_balance
  print(f"\nNet Worth: \033[38;2;0;255;255m${net_worth:,.2f}\033[0m\n")

def __is_income_payment(incomes: List[IncomeStream], today: date) -> bool:
  for income in incomes:
    if income.is_payment_today(today):
      return True
  return False

def __is_asset_appreciation(assets: List[Asset], today: date) -> bool:
  for asset in assets:
    if asset.appreciates_today(today):
      return True
  return False

def __is_account_interest(accounts: List[Account], today: date) -> bool:
  for account in accounts:
    if account.is_interest_today(today):
      return True
  return False

def __is_capital_gains(accounts: List[Account], today: date) -> bool:
  for account in accounts:
    if account.is_capital_gains_today(today):
      return True
  return False

def __is_bill_charge(bills: List[Bill], today: date) -> bool:
  for bill in bills:
    if bill.is_charge_today(today):
      return True
  return False

def __is_bill_charge_increase(bills: List[Bill], today: date) -> bool:
  for bill in bills:
    if bill.increases_today(today):
      return True
  return False

def __is_income_charge_increase(incomes: List[IncomeStream], today: date) -> bool:
  for income in incomes:
    if income.increases_today(today):
      return True
  return False

def __is_debt_interest(debts: List[Debt], today: date) -> bool:
  for debt in debts:
    if debt.is_interest_today(today):
      return True
  return False

def __is_debt_charge(debts: List[Debt], today: date) -> bool:
  for debt in debts:
    if debt.is_charge_today(today):
      return True
  return False

def __get_total_available_funds(age: relativedelta, accounts: List[Account], assets: List[Asset]) -> float:
  running_total = 0
  for account in accounts:
    running_total += account.get_post_tax_balance(age)
  for asset in assets:
    if asset.is_sellable():
      running_total += asset.get_post_tax_value()
  return running_total

def __sell_appropriate_assets(money_needed: float, assets: List[Asset], accounts: List[Account]) -> None:
  sorted_assets = sorted(assets, key=lambda a: a.get_appreciation_rate())
  rolling_money_needed = money_needed
  for account in accounts:
    if account.get_type() == AccountType.INVESTMENT:
      for asset in sorted_assets:
        if asset.is_sellable():
          rolling_money_needed -= asset.get_post_tax_value()
          input(f"\n\033[38;2;255;0;0mWARNING:\033[0m Selling \033[38;2;255;0;0m{asset.get_name()}\033[0m out of desperation.")  # pylint: disable=line-too-long
          sold_assets_worth = asset.sell()
          worth_taken_from_buyer = Buyer.take(sold_assets_worth)
          account.deposit(worth_taken_from_buyer)
          assets.remove(asset)
          if rolling_money_needed <= 0:
            return
  raise BankruptException(rolling_money_needed)

def __handle_tax_day(
  is_print_day: bool,
  is_married: bool,
  age: relativedelta,
  last_years_annual_federal_tax_income_record: AnnualFederalIncomeTaxRecord,
  accounts: List[Account]
) -> None:
  if is_print_day:
    print("Tax Day:")
  tax_return = last_years_annual_federal_tax_income_record.get_annual_tax_returns(is_married)
  if tax_return > 0:
    cash_account = __get_first_cash_account(accounts)
    cash_account.deposit(InternalRevenueService.take(tax_return))
    if is_print_day:
      print(f"  [Tax Day] {cash_account.get_name()}: \033[38;2;0;255;0m+${tax_return:,.2f}\033[0m")
  elif tax_return < 0:
    taxes_owed = abs(tax_return)
    account = __get_first_account_with_amount(age, accounts, taxes_owed)
    InternalRevenueService.give(account.withdraw(taxes_owed, age))
    if is_print_day:
      print(f"  [Tax Day] {account.get_name()}: \033[38;2;255;0;0m-${taxes_owed:,.2f}\033[0m")
  else:
    if is_print_day:
      print("  [Tax Day] No Adjustment")

def __shuffle_funds(age: relativedelta, payment_order: List[List], accounts: List[Account]) -> None:
  __handle_overfilled_accounts(age, payment_order, accounts)
  __handle_underfilled_accounts(age, payment_order, accounts)

def __handle_overfilled_accounts(age: relativedelta, payment_order: List[List], accounts: List[Account]) -> None:
  while True:
    overfilled_account, overfill_amount = __get_overfilled_account(payment_order, accounts)
    if not overfilled_account:
      break
    underfilled_account, _ = __get_underfilled_account(payment_order, accounts)
    if not underfilled_account:
      underfilled_account = __get_first_cash_account(accounts)
    if overfilled_account == underfilled_account:
      break
    underfilled_account.deposit(overfilled_account.withdraw(overfill_amount, age))

def __handle_underfilled_accounts(age: relativedelta, payment_order: List[List], accounts: List[Account]) -> None:
  while True:
    underfilled_account, amount_missing = __get_underfilled_account(payment_order, accounts)
    if not underfilled_account:
      break
    account_with_spare_funds, amount_spare = __get_account_with_spare_funds(age, payment_order, accounts)
    if not account_with_spare_funds:
      break
    if account_with_spare_funds == underfilled_account:
      break
    if amount_spare > amount_missing:
      underfilled_account.deposit(account_with_spare_funds.withdraw(amount_missing, age))
    else:
      underfilled_account.deposit(account_with_spare_funds.withdraw(amount_spare, age))

def __get_overfilled_account(payment_order: List[List], accounts: List[Account]) -> tuple[Account | None, float]:
  account_type_order = [AccountType.CASH, AccountType.SAVINGS, AccountType.INVESTMENT]
  for current_account_type_order in account_type_order:
    for account in accounts:
      if not account.get_type() == current_account_type_order:
        continue
      point_of_overfill = __get_point_of_overfill(payment_order, account)
      if not point_of_overfill:
        continue
      overfill = account.get_balance() - point_of_overfill
      if overfill > 1000:
        return account, overfill
  return None, 0.0

def __get_underfilled_account(payment_order: List[List], accounts: List[Account]) -> tuple[Account | None, float]:
  for current in payment_order:
    current_order_account_name: str = current[0]
    point_of_overfill: float | None = current[1]
    if not point_of_overfill:
      continue
    for account in accounts:
      if not account.get_name().lower() == current_order_account_name.lower():
        continue
      amount_missing = point_of_overfill - account.get_balance()
      if amount_missing > 1000:
        return account, amount_missing
  return None, 0.0

def __get_first_cash_account(accounts: List[Account]) -> Account:
  for account in accounts:
    if account.get_type() == AccountType.CASH:
      return account
  raise RuntimeError("Must provide at least 1 cash account.")

def __get_account_with_spare_funds(
  age: relativedelta,
  payment_order: List[List],
  accounts: List[Account]
) -> tuple[Account | None, float]:
  account_type_order = [AccountType.CASH, AccountType.SAVINGS]
  for current_account_type_order in account_type_order:
    for account in accounts:
      if not account.get_type() == current_account_type_order:
        continue
      point_of_overfill = __get_point_of_overfill(payment_order, account)
      if not point_of_overfill:
        return account, account.get_post_tax_balance(age)
      overfill = account.get_balance() - point_of_overfill
      if overfill > 1000:
        return account, overfill
  return None, 0.0

def __get_point_of_overfill(payment_order: List[List], account: Account) -> float | None:
  highest_point_of_overfill = 0.0
  for current in payment_order:
    ordered_account_name: str = current[0]
    point_of_overfill: float | None = current[1]
    if not account.get_name().lower() == ordered_account_name.lower():
      continue
    if point_of_overfill is None:
      return None
    if point_of_overfill > highest_point_of_overfill:
      highest_point_of_overfill = point_of_overfill
  if highest_point_of_overfill == 0.0:
    return None
  return highest_point_of_overfill

def __build_accounting_record(accounts: List[Account]) -> AccountingRecord:
  user_balances = 0.0
  for account in accounts:
    user_balances += account.get_balance()
  accounting_record = AccountingRecord()
  accounting_record.bank = Bank.peak_balance()
  accounting_record.biller = Biller.peak_balance()
  accounting_record.buyer = Buyer.peak_balance()
  accounting_record.city_government = CityGovernment.peak_balance()
  accounting_record.debtor = Debtor.peak_balance()
  accounting_record.department_of_social_security = DepartmentOfSocialSecurity.peak_balance()
  accounting_record.employer = Employer.peak_balance()
  accounting_record.internal_revenue_service = InternalRevenueService.peak_balance()
  accounting_record.healthcare_provider = HealthcareProvider.peak_balance()
  accounting_record.state_government = StateGovernment.peak_balance()
  accounting_record.stock_market = StockMarket.peak_balance()
  accounting_record.us_treasury = UsTreasury.peak_balance()
  accounting_record.user = user_balances
  return accounting_record

def __get_first_account_with_amount(age: relativedelta, accounts: List[Account], amount: float) -> Account:
  for account in accounts:
    if account.get_post_tax_balance(age) > amount:
      return account
  raise BankruptException(amount)


main()
