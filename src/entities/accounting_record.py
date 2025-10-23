class AccountingRecord:
  bank: float
  biller: float
  buyer: float
  city_government: float
  debtor: float
  department_of_social_security: float
  employer: float
  internal_revenue_service: float
  healthcare_provider: float
  state_government: float
  stock_market: float
  us_treasury: float
  user: float

  def get_current_circulation(self) -> float:
    return (
      self.bank
      + self.biller
      + self.buyer
      + self.city_government
      + self.debtor
      + self.department_of_social_security
      + self.employer
      + self.internal_revenue_service
      + self.healthcare_provider
      + self.state_government
      + self.stock_market
      + self.us_treasury
      + self.user
    )
