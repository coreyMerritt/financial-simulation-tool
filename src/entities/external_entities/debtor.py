class Debtor:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return Debtor.balance

  @staticmethod
  def take(amount: float) -> float:
    Debtor.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    Debtor.balance += amount
