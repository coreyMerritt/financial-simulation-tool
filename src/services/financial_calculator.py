from datetime import date
from typing import List, Tuple
import numpy_financial as npf


class FinancialCalculator:
  @staticmethod
  def calculate_federal_tax(is_married: bool, gross_income: float) -> float:
    if is_married:
      standard_deduction = 29200  # 2025 married filing jointly
      brackets: List[Tuple[float, float, float]] = [
        (0, 23200, 0.10),
        (23200, 94300, 0.12),
        (94300, 201050, 0.22),
        (201050, 383900, 0.24),
        (383900, 487450, 0.32),
        (487450, 731200, 0.35),
        (731200, float('inf'), 0.37)
      ]
    else:
      standard_deduction = 14600  # 2025 single
      brackets = [
        (0, 11600, 0.10),
        (11600, 47150, 0.12),
        (47150, 100525, 0.22),
        (100525, 191950, 0.24),
        (191950, 243725, 0.32),
        (243725, 609350, 0.35),
        (609350, float('inf'), 0.37)
      ]
    taxable_income = max(0, gross_income - standard_deduction)
    tax = 0.0
    for lower, upper, rate in brackets:
      if taxable_income > lower:
        taxed_amount = min(taxable_income, upper) - lower
        tax += taxed_amount * rate
      else:
        break
    return tax

  @staticmethod
  def get_minimum_monthly_payment(
    interest_rate: float,
    principal: float,
    start_date: date,
    end_date: date
  ) -> float:
    years = (end_date - start_date).days / 365
    r = (interest_rate / 100) / 12
    n = years * 12
    return float(abs(npf.pmt(rate=r, nper=n, pv=principal)))

  @staticmethod
  def get_interest(
    principal: float,
    interest_rate: float,
    last_interest_date: date,
    today: date,
  ) -> float:
    """
    Compounds interest daily over the period between `last_interest_date` and `today`.
    This matches real-world interest accumulation.
    """
    if interest_rate == 0 or today <= last_interest_date:
      return 0.0
    days_elapsed = (today - last_interest_date).days
    daily_rate = (interest_rate / 100) / 365
    base = 1 + daily_rate
    if base <= 0:
      return principal * daily_rate * days_elapsed  # fallback to simple interest if negative rate
    return principal * (base ** days_elapsed - 1)
