class InternalRevenueService:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return InternalRevenueService.balance

  @staticmethod
  def take(amount: float) -> float:
    InternalRevenueService.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    InternalRevenueService.balance += amount
