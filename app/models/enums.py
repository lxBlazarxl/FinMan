from enum import Enum


class UserRole(str, Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class AccountType(str, Enum):
    BANK = "BANK"
    CASH = "CASH"
    WALLET = "WALLET"
    CREDIT_CARD = "CREDIT_CARD"


class TransactionType(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"
