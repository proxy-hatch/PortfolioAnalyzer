import logging
from datetime import datetime
from typing import Optional
from lib.model.enum.stage import Stage
from lib.logger.logger import initialize_logger
from lib.ingestion.ingest_baseline import ingest_baseline
from lib.ingestion.ingest_transaction import ingest_transaction

from lib.dash.dash import create_dash_app

logger: Optional[logging.Logger] = None

STATEMENTS_FILEPATH = '../data/statements'
BASELINE_DATE = '2024-01-31'
DEBUG = True


def main() -> None:
    logger.info("Begin analysis.")

    baseline_date = datetime.strptime(BASELINE_DATE, '%Y-%m-%d')
    baseline_df = ingest_baseline(date=baseline_date, filepath=STATEMENTS_FILEPATH)
    # logger.debug("baseline_df: %s", baseline_df.to_string())

    for key, value in baseline_df.items():
        logger.debug("key: %s, value: %s", key, value.to_string())

    logger.debug("baseline_df type: %s", type(baseline_df))


if __name__ == "__main__":
    logger = initialize_logger(Stage.DEV)
    main()
