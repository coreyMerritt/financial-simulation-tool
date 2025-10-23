class Employer:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return Employer.balance

  @staticmethod
  def take(amount: float) -> float:
    Employer.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    Employer.balance += amount
