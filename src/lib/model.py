from dataclasses import dataclass
from enum import Enum


@dataclass
class Position:
    """Class to represent a position."""
    quantity: float
    price: float


class AccountCategory(Enum):
    """Enum for account categories."""
    MARGIN = "Margin"
    TFSA_RRSP = "TFSA_RRSP"

    @staticmethod
    def categorize(account_type: str) -> "AccountCategory":
        return AccountCategory.MARGIN if "Margin" in account_type else AccountCategory.TFSA_RRSP
