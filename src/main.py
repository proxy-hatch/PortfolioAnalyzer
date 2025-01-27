import argparse
import sys
from dataclasses import asdict
from typing import Optional, List
import pandas as pd

from lib.metric_processor.capital_gain import CapitalGainProcessor
from lib.metric_processor.dividend import DividendProcessor
from lib.model.enum.account_category import AccountCategory
from lib.model.enum.stage import Stage
from lib.logger.logger import initialize_logger

logger = None
# logger = logging.getLogger(__name__)
# logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s")
FILE_PATH = '../data/tst.csv'


def preprocess_data(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='%Y-%m-%d %I:%M:%S %p')
    df = df[~df['Description'].str.contains('DLR', case=False, na=False)]
    df = df[~df['Currency'].str.contains('CAD', case=False, na=False)]
    df['Account Category'] = df['Account Type'].apply(AccountCategory.categorize)
    df = df.sort_values(by='Transaction Date').reset_index(drop=True)
    return df


def process(df: pd.DataFrame, start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
    results = []
    start_date = pd.to_datetime(start_date) if start_date else df['Transaction Date'].min()
    end_date = pd.to_datetime(end_date) if end_date else df['Transaction Date'].max()
    processors = [CapitalGainProcessor(), DividendProcessor()]

    for account_category in AccountCategory:
        account_data = df[df['Account Category'] == account_category]
        summary = {'Account Category': account_category.value}

        for processor in processors:
            processor_result = processor.process(account_data, start_date, end_date)
            if isinstance(processor, CapitalGainProcessor):
                processor_result_dict = asdict(processor_result)
                processor_result_dict.pop('daily_realized_gain', None)
                summary.update(processor_result_dict)
            else:
                summary.update(processor_result)

        results.append(summary)

    return pd.DataFrame(results)


def main(start_date: Optional[str], end_date: Optional[str]) -> None:
    logger.info("Starting realized gain calculation.")
    df = preprocess_data(FILE_PATH)
    results = process(df, start_date, end_date)
    logger.info("Calculation completed. Results:")
    print(results)
    # results.to_csv('realized_gain_results.csv', index=False)
    logger.info("Results saved to 'realized_gain_results.csv'.")


def start(args: List[str]) -> None:
    parser = argparse.ArgumentParser(description="Realized Gain Calculator")
    parser.add_argument("-s", "--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("-e", "--end-date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode (print debug log)")
    args = parser.parse_args(args)

    global logger
    if args.verbose:
        logger = initialize_logger(Stage.DEV)
        logger.info("Running in verbose mode.")
    else:
        logger = initialize_logger(Stage.PROD)

    main(start_date=args.start_date, end_date=args.end_date)


if __name__ == "__main__":
    start(sys.argv[1:])
