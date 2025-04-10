import logging
import os
from datetime import datetime
from typing import Optional, Dict
import pandas as pd
from lib.model.enum.account_category import AccountCategory
from lib.model.enum.account_name import AccountName
from lib.logger.logger import get_logger

def ingest_baseline(date: datetime.date, filepath: str) -> Dict[str, pd.DataFrame]:
    """
    Preprocess the baseline data for the given date.

    :param date: The date for which the baseline data is to be processed.
    :param filepath: The directory path where the CSV files are located.
    :return: A dictionary with account name as key and a pandas DataFrame as value.
    """
    logger = get_logger()
    result = {}

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

        result[account_name.name] = df

    return result