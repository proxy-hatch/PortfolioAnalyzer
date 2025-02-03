import os
from datetime import datetime

import pandas as pd

from lib.model.enum.account_category import AccountCategory
from lib.model.enum.account_name import AccountName

from lib.logger.logger import get_logger


def get_baseline_holdings(date: datetime.date,
                          filepath: str,
                          ) -> dict[AccountCategory, pd.DataFrame]:
    """
    Preprocess the baseline data for the given date.

    :param filepath:
    :param date:
    :return:
    """
    logger = get_logger()
    df_ret = pd.DataFrame()

    for account_name in AccountName:
        path = f'{filepath}/{account_name.lower()}-{date.strftime("%Y%m%d")}.csv'
        if not os.path.exists(path):
            logger.error(f'File {path} does not exist.')
            continue

        df = pd.read_csv(path)
        if account_name == AccountName.TFSA or account_name == AccountName.RRSP:
            df['Account Category'] = AccountCategory.TFSA_RRSP
        else:
            df['Account Category'] = AccountCategory.MARGIN

        df_ret = pd.concat([df_ret, df], ignore_index=True)

    # dedupe same symbol in TFSA and RRSP accounts
    df_ret['TotalCost'] = df_ret['Quantity'] * df_ret['AverageCost']
    df_merged = df_ret.groupby(['Symbol', 'Account Category'], as_index=False).agg({
        'Quantity': 'sum',  # Sum the quantities
        'TotalCost': 'sum'  # Sum the total costs
    })
    df_merged['AverageCost'] = df_merged['TotalCost'] / df_merged['Quantity']
    df_merged = df_merged.drop(columns=['TotalCost'])

    return df_merged
