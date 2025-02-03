from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional, Dict

import pandas as pd

from lib.logger.logger import get_logger

from lib.metric_processor.capital_gain import CapitalGainProcessor
from lib.metric_processor.dividend import DividendProcessor
from lib.model.enum.account_category import AccountCategory


@dataclass
class MetricsResult:
    """
    Data class to represent the result of the metrics calculation.

    """
    summary: Dict[str, any]
    daily_realized: pd.DataFrame
    daily_realized_symbols: pd.DataFrame

def process_metrics(txn_df: pd.DataFrame,
                    holdings_df: pd.DataFrame,
                    start_date: datetime.date,
                    end_date: datetime.date) -> MetricsResult:
    """
    Process the transaction data to calculate various metrics for the given date range.

    :param txn_df: DataFrame containing transaction data.
    :param holdings_df: DataFrame containing latest holdings data.
    :param start_date: The start date for the metrics calculation.
    :param end_date: The end date for the metrics calculation.
    """
    results = {}

    processors = [CapitalGainProcessor(holdings_df), DividendProcessor()]

    summary = {}
    daily_realized_df = None
    daily_realized_symbols_df = None

    account_data = txn_df
    for processor in processors:
        processor_result = processor.process(account_data, start_date, end_date)
        processor_result_dict = asdict(processor_result)
        if isinstance(processor, CapitalGainProcessor):
            daily_realized_df = processor_result_dict.pop('daily_realized')
            daily_realized_symbols_df = processor_result_dict.pop('daily_realized_symbols')

        summary.update(processor_result_dict)

    return MetricsResult(summary, daily_realized_df, daily_realized_symbols_df)
