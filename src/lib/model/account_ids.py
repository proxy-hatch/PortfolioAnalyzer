from lib.model.enum.account_name import AccountName

ACCOUNT_ID_ACCOUNT_NAME_MAP = {
    51976038: AccountName.RRSP,
    51973067: AccountName.TFSA,
    27305856: AccountName.MARGIN
}

ACCOUNT_NAME_ACCOUNT_ID_MAP = {v: k for k, v in ACCOUNT_ID_ACCOUNT_NAME_MAP.items()}