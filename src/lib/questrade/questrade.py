from datetime import datetime

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

    def get_holdings(self, account_category: AccountCategory) -> pd.DataFrame:
        """
        Retrieve holdings for account category and return as DataFrame.

        :return: pd.DataFrame - Dataframe with columns: ['Symbol', 'OpenQuantity', 'CurrentMarketValue', 'CurrentPrice', 'AverageEntryPrice', 'OpenPnl', 'TotalCost']
        Sample Output:
            Symbol  OpenQuantity  CurrentMarketValue  CurrentPrice      OpenPnl     TotalCost  AverageEntryPrice
        0    AAPL            61            14396.00        236.00   832.680012  13563.319988         222.349508
        1     AMD            16             1855.20        115.95 -1064.640000   2919.840000         182.490000
        2    AMZN            30             7130.40        237.68   722.382000   6408.018000         213.600600
        """
        if account_category == AccountCategory.TFSA_RRSP:
            tfsa_df = self._get_holdings_by_account(AccountName.TFSA)
            rrsp_df = self._get_holdings_by_account(AccountName.RRSP)

            df_ret = pd.concat([tfsa_df, rrsp_df], ignore_index=True)

            # dedupe the same symbol in TFSA and RRSP accounts
            df_merged = df_ret.groupby(['Symbol'], as_index=False).agg({
                'OpenQuantity': 'sum',  # Sum the quantities
                'CurrentMarketValue': 'sum',  # Sum the market values
                'CurrentPrice': 'first',
                'OpenPnl': 'sum',  # Sum the open PnL
                'TotalCost': 'sum',  # Sum the total costs
            })
            df_merged['AverageEntryPrice'] = df_merged['TotalCost'] / df_merged['OpenQuantity']
            return df_merged
        elif account_category == AccountCategory.MARGIN:
            return self._get_holdings_by_account(AccountName.MARGIN)
        else:
            raise ValueError(f"Unsupported account category: {account_category}")

    def get_account_activities(
            self, account_category: AccountCategory, start_date: datetime.date, end_date: datetime.date
    ) -> pd.DataFrame:
        """
        Retrieve account activities for the given account category and date range and return as a Pandas DataFrame.

        ### Columns in Returned DataFrame:
        - **Date (datetime64[ns])**: The settlement date of the transaction.
        - **Action (str)**: The type of action (e.g., 'Buy', 'Sell', 'DIV', 'WDR', 'TF6', etc.).
        - **Symbol (str)**: The stock/ETF ticker symbol involved in the transaction.
        - **Description (str)**: A textual description of the transaction.
        - **Currency (str)**: The currency used for the transaction (e.g., 'USD', 'CAD').
        - **Quantity (float)**: The number of shares involved in the transaction.
        - **Price (float)**: The price per unit of the security.
        - **Gross Amount (float)**: The total value of the transaction before commissions.
        - **Commission (float)**: The fee charged for the transaction.
        - **Net Amount (float)**: The total transaction value after deducting commissions.
        - **Type (str)**: The category of transaction, e.g., 'Trades', 'Dividends', 'Transfers', etc.

        :param account_category:
        :param start_date:
        :param end_date:
        :return:
        Sample Output:
                                Date Action Symbol                                                                                                          Description Currency  Quantity     Price  GrossAmount  Commission  NetAmount       Type
        0 2024-12-04 00:00:00-05:00    Buy   AMZN                                                                                    AMAZON.COM INC  WE ACTED AS AGENT      USD        30  213.6006     -6408.02       -4.95   -6412.97     Trades
        7 2024-12-11 00:00:00-05:00    Buy  BRK.B                                                                  BERKSHIRE HATHAWAY INC DEL  CL B  WE ACTED AS AGENT      USD        16  460.8900     -7374.24       -4.95   -7379.19     Trades
        1 2024-12-12 00:00:00-05:00    DIV   MSFT                            MICROSOFT CORP  CASH DIV  ON      26 SHS  REC 11/21/24 PAY 12/12/24  NON-RES TAX WITHHELD      USD         0    0.0000         0.00        0.00      18.35  Dividends
        2 2024-12-16 00:00:00-05:00    DIV   GOOG       ALPHABET INC  CLASS C CAPITAL STOCK  CASH DIV  ON      63 SHS  REC 12/09/24 PAY 12/16/24  NON-RES TAX WITHHELD      USD         0    0.0000         0.00        0.00      10.71  Dividends
        5 2024-12-18 00:00:00-05:00    Buy    ETN                                             EATON CORPORATION PLC  WE ACTED AS AGENT  AVG PRICE - ASK US FOR DETAILS      USD        12  349.7100     -4196.52       -4.95   -4201.47     Trades
        """
        if account_category == AccountCategory.TFSA_RRSP:
            tfsa_df = self._get_account_activities_by_account(AccountName.TFSA, start_date, end_date)
            rrsp_df = self._get_account_activities_by_account(AccountName.RRSP, start_date, end_date)
            df = pd.concat([tfsa_df, rrsp_df], ignore_index=True)

            return df.sort_values(by='Date')

        elif account_category == AccountCategory.MARGIN:
            return self._get_account_activities_by_account(AccountName.MARGIN, start_date, end_date).sort_values(
                by='Date')
        else:
            raise ValueError(f"Unsupported account category: {account_category}")

    def _get_holdings_by_account(self, account_name: AccountName) -> pd.DataFrame:
        """
        Retrieve holdings for the account and return as DataFrame.

        :return: pd.DataFrame - Dataframe with columns: ['Symbol', 'OpenQuantity', 'CurrentMarketValue', 'CurrentPrice', 'AverageEntryPrice', 'OpenPnl', 'TotalCost']
        """
        positions = self.client.get_account_positions(ACCOUNT_NAME_ACCOUNT_ID_MAP[account_name])
        df = pd.DataFrame(positions)
        df = df.drop(columns=['symbolId', 'dayPnl', 'closedPnl', 'isRealTime', 'isUnderReorg'])

        df.columns = [word[0].upper() + word[1:] for word in df.columns]
        return df

    def _get_account_activities_by_account(
            self, account: AccountName, start_date: datetime.date, end_date: datetime.date
    ) -> pd.DataFrame:
        """
        Retrieve account activities for the given account and date range and return as a Pandas DataFrame.

        The returned DataFrame contains details about transactions such as trades, dividends, and other financial activities.

        ### Columns in Returned DataFrame:
        - **Date (datetime64[ns])**: The settlement date of the transaction.
        - **Action (str)**: The type of action (e.g., 'Buy', 'Sell', 'DIV', 'WDR', 'TF6', etc.).
        - **Symbol (str)**: The stock/ETF ticker symbol involved in the transaction.
        - **Description (str)**: A textual description of the transaction.
        - **Currency (str)**: The currency used for the transaction (e.g., 'USD', 'CAD').
        - **Quantity (float)**: The number of shares involved in the transaction.
        - **Price (float)**: The price per unit of the security.
        - **Gross Amount (float)**: The total value of the transaction before commissions.
        - **Commission (float)**: The fee charged for the transaction.
        - **Net Amount (float)**: The total transaction value after deducting commissions.
        - **Type (str)**: The category of transaction, e.g., 'Trades', 'Dividends', 'Transfers', etc.

        :param account: AccountName - The account to retrieve activities for.
        :param start_date: datetime.date - The start date of the date range.
        :param end_date: datetime.date - The end date of the date range.
        :return: pd.DataFrame - A structured DataFrame containing transactions for the given account and date range.
        """

        result = self.client.get_account_activities(
            ACCOUNT_NAME_ACCOUNT_ID_MAP[account],
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )

        # Convert the result to a Pandas DataFrame
        df = pd.DataFrame(result)

        if df.empty:
            self.logger.info(f"No activities found for {account} in date range {start_date} to {end_date}.")
            return df

        # Drop unwanted columns
        df.drop(columns=['tradeDate', 'transactionDate', 'symbolId'], inplace=True, errors='ignore')

        # Rename columns
        df.rename(columns={'settlementDate': 'Date'}, inplace=True)

        # Convert 'Date' column to Pandas Timestamp
        df['Date'] = pd.to_datetime(df['Date'])
        df.columns = [word[0].upper() + word[1:] for word in df.columns]

        self.logger.debug(f"Processed activities for {account}:\n{df.head()}")

        return df
