class CityGovernment:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return CityGovernment.balance

  @staticmethod
  def take(amount: float) -> float:
    CityGovernment.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    CityGovernment.balance += amount
