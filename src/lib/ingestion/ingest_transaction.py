import pandas as pd

from lib.model.enum.account_category import AccountCategory


def ingest_transaction(filepath: str) -> pd.DataFrame:
    """
    Preprocess the transaction data by
    - filtering out DLR and CAD transactions.
    - categorize the account type.
    - sort by Settlement date, and keep this column as 'Date'.

    :param filepath:
    :return:
    """
    df = pd.read_csv(filepath)
    df['Date'] = pd.to_datetime(df['Settlement Date'], format='%Y-%m-%d %I:%M:%S %p')
    df = df[~df['Description'].str.contains('DLR', case=False, na=False)]
    df = df[~df['Currency'].str.contains('CAD', case=False, na=False)]
    df['Account Category'] = df['Account Type'].apply(AccountCategory.categorize)
    df = df.sort_values(by='Date').reset_index(drop=True)
    return df
