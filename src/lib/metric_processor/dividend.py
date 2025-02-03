from dataclasses import dataclass
from typing import Dict

import pandas as pd

from lib.metric_processor.base import BaseProcessor


@dataclass
class DividendResult:
    total_dividends: float


class DividendProcessor(BaseProcessor):
    # ignore additional positional and keyword arguments
    def process(self, txn_df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp,
                *args, **kwargs) -> DividendResult:
        dividends = txn_df[txn_df['Activity Type'] == 'Dividends']
        total_dividends = dividends[
            (dividends['Date'] >= start_date) & (dividends['Date'] <= end_date)
            ]['Net Amount'].sum()
        return DividendResult(total_dividends=total_dividends)
