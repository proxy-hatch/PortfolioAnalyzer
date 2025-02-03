import pandas as pd
from qtrade import Questrade

from lib.logger.logger import get_logger
from lib.model.account_ids import ACCOUNT_NAME_ACCOUNT_ID_MAP
from lib.model.enum.account_category import AccountCategory
from lib.model.enum.account_name import AccountName

REFRESH_TOKEN = 'ApnS9SC91BMppo1_hwUGsktx4v95KgkJ0'
ACCESS_TOKEN_PATH = './access_token.yml'


class QuestradeInterface:
    def __init__(self):
        self.client = Questrade(token_yaml=ACCESS_TOKEN_PATH)
        self.client.refresh_access_token(from_yaml=True)
        self.logger = get_logger()

    def get_holdings(self) -> dict[AccountCategory, pd.DataFrame]:
        """
        Retrieve holdings for each account category and return as a dictionary of DataFrames.

        :return: dict[AccountCategory, pd.DataFrame] - A dictionary where keys are AccountName and values are DataFrames
                 with columns: ['symbol', 'openQuantity', 'currentMarketValue', 'currentPrice', 'averageEntryPrice', 'openPnl', 'totalCost']
        """
        holdings_by_account = self._get_holdings_by_account()

        for account_name, df in holdings_by_account.items():
            self.logger.debug(f"holdings for {account_name} are {df.head(50)}")

        df_ret = pd.concat([holdings_by_account[AccountName.TFSA], holdings_by_account[AccountName.RRSP]],
                           ignore_index=True)

        # dedupe the same symbol in TFSA and RRSP accounts
        df_merged = df_ret.groupby(['symbol'], as_index=False).agg({
            'openQuantity': 'sum',  # Sum the quantities
            'currentMarketValue': 'sum',  # Sum the market values
            'currentPrice': 'first',
            'openPnl': 'sum',  # Sum the open PnL
            'totalCost': 'sum',  # Sum the total costs
        })
        df_merged['averageEntryPrice'] = df_merged['totalCost'] / df_merged['openQuantity']

        self.logger.debug(f"merged holdings for TFSA_RRSP are {df_merged.head(50)}")

        return {
            AccountCategory.TFSA_RRSP: df_merged,
            AccountCategory.MARGIN: holdings_by_account[AccountName.MARGIN]
        }

    def _get_holdings_by_account(self) -> dict[AccountName, pd.DataFrame]:
        """
        Retrieve holdings for each account and return as a dictionary of DataFrames.

        :return: dict[AccountName, pd.DataFrame] - A dictionary where keys are AccountName and values are DataFrames
                 with columns: ['symbol', 'openQuantity', 'currentMarketValue', 'currentPrice', 'averageEntryPrice', 'openPnl', 'totalCost']
        """
        holdings = {}
        for account_name, account_id in ACCOUNT_NAME_ACCOUNT_ID_MAP.items():
            positions = self.client.get_account_positions(account_id)
            df = pd.DataFrame(positions)
            df = df.drop(columns=['symbolId', 'dayPnl', 'closedPnl', 'isRealTime', 'isUnderReorg'])
            holdings[account_name] = df

        return holdings
