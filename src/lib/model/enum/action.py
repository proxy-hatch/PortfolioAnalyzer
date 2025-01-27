from enum import StrEnum
from typing import Optional


class Action(StrEnum):
    BUY = 'Buy'
    SELL = 'Sell'
    DIV = 'DIV'