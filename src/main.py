import argparse
import logging
import os
import sys
from dataclasses import asdict
from datetime import datetime
from typing import Optional, List
import pandas as pd

from lib.metric_processor.capital_gain import CapitalGainProcessor
from lib.metric_processor.dividend import DividendProcessor
from lib.model.enum.account_category import AccountCategory
from lib.model.enum.stage import Stage
from lib.logger.logger import initialize_logger
from lib.model.enum.account_name import AccountName

logger: Optional[logging.Logger] = None
FILEPATH = '../data/all_txns.csv'
STATEMENTS_FILEPATH = '../data/statements'


def preprocess_txn(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%Y-%m-%d %I:%M:%S %p')
    df = df[~df['Description'].str.contains('DLR', case=False, na=False)]
    df = df[~df['Currency'].str.contains('CAD', case=False, na=False)]
    df['Account Category'] = df['Account Type'].apply(AccountCategory.categorize)
    df = df.sort_values(by='Transaction Date').reset_index(drop=True)
    return df


def preprocess_baseline(date: datetime.date) -> pd.DataFrame:
    """
    Preprocess the baseline data for the given date.

    :param date:
    :return:
    """
    df_ret = pd.DataFrame()

    for account_name in AccountName:
        filepath = f'{STATEMENTS_FILEPATH}/{account_name.lower()}-{date.strftime("%Y%m%d")}.csv'
        if not os.path.exists(filepath):
            logger.error(f'File {filepath} does not exist.')
            continue

        df = pd.read_csv(filepath)
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


def process(txn_df: pd.DataFrame,
            holdings_df: pd.DataFrame,
            holdings_date: datetime.date,
            start_date: Optional[str],
            end_date: Optional[str]) -> pd.DataFrame:
    """
    Process the transaction data to calculate various metrics for the given date range.

    :param txn_df:
    :param holdings_df:
    :param holdings_date:
    :param start_date:
    :param end_date:
    :return:
    """
    results = []
    start_date = pd.to_datetime(start_date) if start_date else txn_df['Transaction Date'].min()
    end_date = pd.to_datetime(end_date) if end_date else txn_df['Transaction Date'].max()
    if holdings_date > start_date:
        logger.error(f"Holdings date {holdings_date} is after start date {start_date}.")
        raise ValueError(f"Holdings date {holdings_date} is after start date {start_date}.")

    processors = [CapitalGainProcessor(holdings_df, holdings_date), DividendProcessor()]

    for account_category in AccountCategory:
        account_data = txn_df[txn_df['Account Category'] == account_category]
        summary = {'Account Category': account_category.value}

        for processor in processors:
            processor_result = processor.process(account_data, start_date, end_date, account_category)
            if isinstance(processor, CapitalGainProcessor):
                processor_result_dict = asdict(processor_result)
                processor_result_dict.pop('daily_realized_gain', None)
                summary.update(processor_result_dict)
            else:
                summary.update(processor_result)

        results.append(summary)

    return pd.DataFrame(results)


def main(start_date: Optional[str], end_date: Optional[str], baseline_date: str) -> None:
    logger.info("Begin analysis.")

    baseline_date = datetime.strptime(baseline_date, '%Y-%m-%d')
    baseline_df = preprocess_baseline(date=baseline_date)
    txn_df = preprocess_txn(FILEPATH)

    results = process(txn_df=txn_df, holdings_df=baseline_df, start_date=start_date, end_date=end_date,
                      holdings_date=baseline_date)

    logger.info("Calculation completed. Results:")
    logger.info(results)
    # results.to_csv('realized_gain_results.csv', index=False)
    logger.info("Results saved to 'realized_gain_results.csv'.")


def start(args: List[str]) -> None:
    parser = argparse.ArgumentParser(description="Realized Gain Calculator")
    parser.add_argument("-s", "--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("-e", "--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("-b", "--baseline-date", required=True, type=str,
                        help="Baseline date to provide the script with holdings info. The script will look for the "
                             "files data/statements/{tfsa|rrsp|margin}-YYYYMMDD.csv (YYYY-MM-DD)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode (print debug log)")

    args = parser.parse_args(args)

    global logger
    if args.verbose:
        logger = initialize_logger(Stage.DEV)
        logger.info("Running in verbose mode.")
    else:
        logger = initialize_logger(Stage.PROD)

    main(start_date=args.start_date, end_date=args.end_date, baseline_date=args.baseline_date)


if __name__ == "__main__":
    start(sys.argv[1:])
