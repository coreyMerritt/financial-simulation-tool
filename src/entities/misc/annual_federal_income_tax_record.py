from services.financial_calculator import FinancialCalculator


class AnnualFederalIncomeTaxRecord:
  __income: float = 0.0
  __tax_paid: float = 0.0

  def get_income(self) -> float:
    return self.__income

  def get_tax_paid(self) -> float:
    return self.__tax_paid

  def get_annual_tax_returns(self, is_married: bool) -> float:
    tax_owed = FinancialCalculator.calculate_federal_tax(is_married, self.__income)
    tax_return = self.__tax_paid - tax_owed
    return tax_return

  def add_income(self, amount: float) -> None:
    self.__income += amount

  def add_tax_paid(self, amount: float) -> None:
    self.__tax_paid += amount

  def reset_income(self) -> None:
    self.__income = 0.0

  def reset_tax_paid(self) -> None:
    self.__tax_paid = 0.0
