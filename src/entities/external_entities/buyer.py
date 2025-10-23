class Buyer:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return Buyer.balance

  @staticmethod
  def take(amount: float) -> float:
    Buyer.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    Buyer.balance += amount
