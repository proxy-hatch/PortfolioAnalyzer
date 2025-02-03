import logging
from datetime import datetime
from typing import Optional
from lib.model.enum.stage import Stage
from lib.logger.logger import initialize_logger
from lib.ingestion.ingest_baseline import get_current_holdings
from lib.ingestion.ingest_transaction import ingest_transaction

from lib.dash.dash import create_dash_app
from lib.questrade.questrade import QuestradeInterface

logger: Optional[logging.Logger] = None

TXN_FILEPATH = '../data/all_txns.csv'
STATEMENTS_FILEPATH = '../data/statements'
BASELINE_DATE = '2023-12-31'
DEBUG = True


def main() -> None:
    logger.info("Begin analysis.")

    q = QuestradeInterface()
    q.get_holdings()

    #
    # baseline_date = datetime.strptime(BASELINE_DATE, '%Y-%m-%d')
    # baseline_df = get_current_holdings(date=baseline_date, filepath=STATEMENTS_FILEPATH)
    # txn_df = ingest_transaction(TXN_FILEPATH)
    #
    # logger.info("Calculation completed.")
    # # results.to_csv('realized_gain_results.csv', index=False)
    # # logger.info("Results saved to 'realized_gain_results.csv'.")
    # app = create_dash_app(txn_df=txn_df, baseline_df=baseline_df, baseline_date=baseline_date)
    # app.run_server(debug=True)


if __name__ == "__main__":
    logger = initialize_logger(Stage.DEV)
    main()
