import logging
from datetime import datetime
from typing import Optional

import pandas as pd

from lib.metric_processor.processor import process_metrics
from lib.model.enum.account_category import AccountCategory
from lib.model.enum.account_name import AccountName
from lib.model.enum.stage import Stage
from lib.logger.logger import initialize_logger
from lib.ingestion.load_baseline_holdings_csvs import load_baseline_holdings_csvs
from lib.ingestion.ingest_transaction import ingest_transaction

from lib.dash.dash import create_dash_app
from lib.questrade.questrade import QuestradeInterface

logger: Optional[logging.Logger] = None

TXN_FILEPATH = '../data/all_txns.csv'
STATEMENTS_FILEPATH = '../data/statements'
BASELINE_DATE = '2024-06-12'
DEBUG = True


def main() -> None:
    logger.info("Begin analysis.")

    baseline_date = datetime.strptime(BASELINE_DATE, '%Y-%m-%d').date()
    txn_start_date = (baseline_date + pd.DateOffset(days=1)).tz_localize(None).date()

    logger.debug(f"Baseline date: {baseline_date}")
    logger.debug(f"Transaction start date: {txn_start_date}")

    # baseline_dfs = load_baseline_holdings_csvs(date=baseline_date, filepath=STATEMENTS_FILEPATH)
    #
    q = QuestradeInterface()
    txn_dfs = q.get_all_account_activities(txn_start_date, datetime.now().date())
    logger.info(f"Transactions retrieved.\n {txn_dfs}")

    # holdings = q.get_holdings(account_category=AccountCategory.TFSA_RRSP)
    # logger.info(f"Holdings retrieved.\n {holdings.to_string()}")

    # start_date = datetime.strptime('2024-12-01', '%Y-%m-%d')
    # end_date = datetime.strptime('2024-12-31', '%Y-%m-%d')
    # activities = q.get_account_activities(account_category=AccountCategory.TFSA_RRSP, start_date=start_date, end_date=end_date)
    # logger.info(f"Activities retrieved.\n {activities.to_string()}")
    #
    # analysis_result = process_metrics(txn_df=txn_df,
    #                                   start_date=pd.to_datetime(start_date),
    #                                   end_date=pd.to_datetime(end_date),
    #                                   # holdings_df=questrade_client.get_holdings(account_category=account_category),
    #                                   baseline_df=baseline_dfs[account_category],
    #                                   baseline_date=baseline_date
    #                                   )
    # logger.info(f"Analysis result updated. {analysis_result}")


    # txn_df = ingest_transaction(TXN_FILEPATH)
    #
    # logger.info("Calculation completed.")
    # # results.to_csv('realized_gain_results.csv', index=False)
    # # logger.info("Results saved to 'realized_gain_results.csv'.")
    # app = create_dash_app(questrade_client=QuestradeInterface(), baseline_dfs=baseline_dfs, baseline_date=baseline_date)
    # app.run_server(debug=True)


if __name__ == "__main__":
    logger = initialize_logger(Stage.DEV)
    main()
