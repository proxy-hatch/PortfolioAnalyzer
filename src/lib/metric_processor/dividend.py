from typing import Dict

import pandas as pd

from lib.metric_processor.base import BaseProcessor


class DividendProcessor(BaseProcessor):
    # ignore additional positional and keyword arguments
    def process(self, df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp,
                *args, **kwargs) -> Dict[str, float]:
        dividends = df[df['Activity Type'] == 'Dividends']
        total_dividends = dividends[
            (dividends['Transaction Date'] >= start_date) & (dividends['Transaction Date'] <= end_date)
            ]['Net Amount'].sum()
        return {'Total Dividends': total_dividends}
