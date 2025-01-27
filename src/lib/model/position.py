from dataclasses import dataclass
from enum import Enum


@dataclass
class Position:
    """Class to represent a position."""
    quantity: float
    avg_price: float

