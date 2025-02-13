import logging
import os
from datetime import datetime
from typing import Optional
from lib.model.enum.stage import Stage
from lib.logger.logger import initialize_logger
from lib.ingestion.ingest_baseline import ingest_baseline
from lib.ingestion.ingest_transaction import ingest_transaction

from lib.dash.dash import create_dash_app
from lib.constant.constant import DEBUG, TXN_FILEPATH, BASELINE_DATE, STATEMENTS_FILEPATH

logger: Optional[logging.Logger] = None

# get stage from environment variable
STAGE = os.getenv('STAGE', Stage.DEV)

def main() -> None:
    logger.info("Begin analysis.")

    baseline_date = datetime.strptime(BASELINE_DATE, '%Y-%m-%d')
    baseline_df = ingest_baseline(date=baseline_date, filepath=STATEMENTS_FILEPATH)
    txn_df = ingest_transaction(TXN_FILEPATH)

    logger.info("Calculation completed.")
    # results.to_csv('realized_gain_results.csv', index=False)
    # logger.info("Results saved to 'realized_gain_results.csv'.")
    app = create_dash_app(txn_df=txn_df, baseline_df=baseline_df, baseline_date=baseline_date)
    app.run_server(host="0.0.0.0", port=8050, debug=DEBUG)


if __name__ == "__main__":
    logger = initialize_logger(STAGE)
    main()
