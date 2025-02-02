from dataclasses import asdict
from datetime import datetime
from typing import Optional, Dict

import pandas as pd

from lib.logger.logger import get_logger

from lib.metric_processor.capital_gain import CapitalGainProcessor
from lib.metric_processor.dividend import DividendProcessor
from lib.model.enum.account_category import AccountCategory


def process_metrics(txn_df: pd.DataFrame,
                    holdings_df: pd.DataFrame,
                    holdings_date: datetime.date,
                    start_date: Optional[str],
                    end_date: Optional[str]) -> Dict[str, pd.DataFrame]:
    """
    Process the transaction data to calculate various metrics for the given date range.

    :param txn_df: DataFrame containing transaction data.
    :param holdings_df: DataFrame containing holdings data.
    :param holdings_date: The date of the holdings data.
    :param start_date: The start date for the metrics calculation (optional).
    :param end_date: The end date for the metrics calculation (optional).
    :return: A dictionary containing two keys:
             - 'summary': A DataFrame summarizing the metrics.
             - 'daily_realized': A DataFrame containing daily realized gains.
             - 'daily_realized_symbols': A DataFrame containing daily realized gains by symbols.

    """
    logger = get_logger()
    daily_realized_df = None
    daily_realized_symbols_df = None

    results = []
    start_date = pd.to_datetime(start_date) if start_date else txn_df['Date'].min()
    end_date = pd.to_datetime(end_date) if end_date else txn_df['Date'].max()
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
                daily_realized_df = processor_result_dict.pop('daily_realized')
                daily_realized_symbols_df = processor_result_dict.pop('daily_realized_symbols')
                summary.update(processor_result_dict)
            else:
                summary.update(processor_result)

        results.append(summary)

    summary_df = pd.DataFrame(results)

    return {
        'summary': summary_df,
        'daily_realized': daily_realized_df,
        'daily_realized_symbols': daily_realized_symbols_df
    }
