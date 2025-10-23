class StateGovernment:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return StateGovernment.balance

  @staticmethod
  def take(amount: float) -> float:
    StateGovernment.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    StateGovernment.balance += amount
