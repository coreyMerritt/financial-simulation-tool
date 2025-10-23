class StockMarket:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return StockMarket.balance

  @staticmethod
  def take(amount: float) -> float:
    StockMarket.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    StockMarket.balance += amount
