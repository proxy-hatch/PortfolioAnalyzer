from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict

import pandas as pd

from lib.metric_processor.capital_gain import CapitalGainProcessor
from lib.metric_processor.dividend import DividendProcessor

from lib.logger.logger import get_logger


@dataclass
class MetricsResult:
    """
    Data class to represent the result of the metrics calculation.

    """
    summary: Dict[str, any]
    daily_realized: pd.DataFrame
    daily_realized_symbols: pd.DataFrame


def process_metrics(txn_df: pd.DataFrame,
                    # holdings_df: pd.DataFrame,
                    start_date: datetime.date,
                    end_date: datetime.date,
                    baseline_df: pd.DataFrame,
                    baseline_date: datetime.date
                    ) -> MetricsResult:
    """
    Process the transaction data to calculate various metrics for the given date range.

    :param baseline_date:
    :param baseline_df:
    :param txn_df: DataFrame containing transaction data from baseline date to end date.
    # :param holdings_df: DataFrame containing latest holdings data.
    :param start_date: The start date for the metrics calculation.
    :param end_date: The end date for the metrics calculation.
    """
    logger = get_logger()
    if baseline_date > start_date:
        logger.error(f"Baseline date {baseline_date} is after start date {start_date}.")
        raise ValueError(f"Baseline date {baseline_date} is after start date {start_date}.")

    processors = [CapitalGainProcessor(), DividendProcessor()]

    summary = {}
    daily_realized_df = None
    daily_realized_symbols_df = None

    account_data = txn_df
    for processor in processors:
        processor_result = processor.process(txn_df=account_data,
                                             start_date=start_date,
                                             end_date=end_date,
                                             # holdings_df=holdings_df,
                                             baseline_df=baseline_df,
                                             baseline_date=baseline_date)
        processor_result_dict = asdict(processor_result)
        if isinstance(processor, CapitalGainProcessor):
            daily_realized_df = processor_result_dict.pop('daily_realized')
            daily_realized_symbols_df = processor_result_dict.pop('daily_realized_symbols')

        summary.update(processor_result_dict)

    return MetricsResult(summary, daily_realized_df, daily_realized_symbols_df)
