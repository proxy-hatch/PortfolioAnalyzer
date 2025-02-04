from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd

from lib.logger.logger import get_logger


class BaseProcessor(ABC):
    def __init__(self):
        self.logger = get_logger()

    @abstractmethod
    def process(self, txn_df: pd.DataFrame,
                start_date: pd.Timestamp, end_date: pd.Timestamp, *args, **kwargs) -> any:
        pass
