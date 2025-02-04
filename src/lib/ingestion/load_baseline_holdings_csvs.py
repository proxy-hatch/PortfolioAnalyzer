import os
from datetime import datetime

import pandas as pd

from lib.model.enum.account_category import AccountCategory
from lib.model.enum.account_name import AccountName

from lib.logger.logger import get_logger


def load_baseline_holdings_csvs(date: datetime.date,
                                filepath: str,
                                ) -> dict[AccountCategory, pd.DataFrame]:
    """
    Preprocess the baseline data for the given date.

    Return a dictionary of dataframes, with the key being the account category and the value being the dataframe.

    Dataframe contains:
    - Symbol
    - Quantity
    - AverageCost
    - TotalCost: Quantity * AverageCost

    :param filepath:
    :param date:
    :return:
    """
    logger = get_logger()
    tfsa_rrsp_df, margin_df = pd.DataFrame(), pd.DataFrame()

    for account_name in AccountName:
        path = f'{filepath}/{account_name.lower()}-{date.strftime("%Y%m%d")}.csv'
        if not os.path.exists(path):
            logger.error(f'File {path} does not exist.')
            continue

        df = pd.read_csv(path)
        if account_name == AccountName.TFSA or account_name == AccountName.RRSP:
            tfsa_rrsp_df = pd.concat([tfsa_rrsp_df, df], ignore_index=True)
        elif account_name == AccountName.MARGIN:
            margin_df = df
        else:
            logger.error(f'Account name {account_name} is not supported.')
            continue

    # dedupe same symbol in TFSA and RRSP accounts
    tfsa_rrsp_df['TotalCost'] = tfsa_rrsp_df['Quantity'] * tfsa_rrsp_df['AverageCost']
    tfsa_rrsp_df = tfsa_rrsp_df.groupby(['Symbol'], as_index=False).agg({
        'Quantity': 'sum',  # Sum the quantities
        'TotalCost': 'sum'  # Sum the total costs
    })
    tfsa_rrsp_df['AverageCost'] = tfsa_rrsp_df['TotalCost'] / tfsa_rrsp_df['Quantity']

    return {
        AccountCategory.TFSA_RRSP: tfsa_rrsp_df,
        AccountCategory.MARGIN: margin_df
    }
