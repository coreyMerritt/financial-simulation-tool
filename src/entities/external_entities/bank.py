class Bank:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return Bank.balance

  @staticmethod
  def take(amount: float) -> float:
    Bank.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    Bank.balance += amount
