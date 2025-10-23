class Biller:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return Biller.balance

  @staticmethod
  def take(amount: float) -> float:
    Biller.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    Biller.balance += amount
