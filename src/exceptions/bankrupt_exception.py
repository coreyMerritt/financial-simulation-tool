class BankruptException(Exception):
  _money_needed: float

  def __init__(self, money_needed: float) -> None:
    super().__init__()
    self._money_needed = money_needed

  def get_money_needed(self) -> float:
    return self._money_needed
