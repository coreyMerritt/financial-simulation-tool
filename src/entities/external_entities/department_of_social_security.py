class DepartmentOfSocialSecurity:
  balance: float = 1000000000

  @staticmethod
  def peak_balance() -> float:
    return DepartmentOfSocialSecurity.balance

  @staticmethod
  def take(amount: float) -> float:
    DepartmentOfSocialSecurity.balance -= amount
    return amount

  @staticmethod
  def give(amount: float) -> None:
    DepartmentOfSocialSecurity.balance += amount
