class HealthcareProvider:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return HealthcareProvider.balance

  @staticmethod
  def take(amount: float) -> float:
    HealthcareProvider.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    HealthcareProvider.balance += amount
