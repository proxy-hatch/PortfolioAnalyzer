from enum import StrEnum


class AccountName(StrEnum):
    """Enum for account names."""
    MARGIN = "Margin"
    TFSA = "TFSA"
    RRSP = "RRSP"
