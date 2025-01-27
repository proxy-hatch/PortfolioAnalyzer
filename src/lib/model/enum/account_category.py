from enum import StrEnum


class AccountCategory(StrEnum):
    """Enum for account categories."""
    MARGIN = "Margin"
    TFSA_RRSP = "TFSA_RRSP"

    @staticmethod
    def categorize(account_type: str) -> "AccountCategory":
        return AccountCategory.MARGIN if "Margin" in account_type else AccountCategory.TFSA_RRSP
