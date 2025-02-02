import argparse
import logging
import sys
from datetime import datetime
from typing import Optional, List

import pandas as pd
from dash import Dash

from lib.model.enum.stage import Stage
from lib.logger.logger import initialize_logger
from lib.ingestion.ingest_baseline import ingest_baseline
from lib.ingestion.ingest_transaction import ingest_transaction
from lib.metric_processor.processor import process_metrics

logger: Optional[logging.Logger] = None
TXN_FILEPATH = '../data/all_txns.csv'
STATEMENTS_FILEPATH = '../data/statements'

#
# def aggregate_monthly_realized(df: pd.DataFrame) -> pd.DataFrame:
#     """
#     Aggregate the total realized gain/loss on a monthly basis.
#     :param df: DataFrame containing the daily realized gain/loss data.
#     :return: DataFrame containing the monthly aggregated realized gain/loss data.
#     """
#     return df.resample('M').sum()

def main(start_date: Optional[str], end_date: Optional[str], baseline_date: str) -> None:
    logger.info("Begin analysis.")

    baseline_date = datetime.strptime(baseline_date, '%Y-%m-%d')
    baseline_df = ingest_baseline(date=baseline_date, filepath=STATEMENTS_FILEPATH)
    txn_df = ingest_transaction(TXN_FILEPATH)

    results = process_metrics(txn_df=txn_df, holdings_df=baseline_df, start_date=start_date, end_date=end_date,
                              holdings_date=baseline_date)


    logger.info("Calculation completed. Results:")
    logger.info(results['summary'])
    # results.to_csv('realized_gain_results.csv', index=False)
    # logger.info("Results saved to 'realized_gain_results.csv'.")


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
