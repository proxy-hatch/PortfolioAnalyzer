from dataclasses import dataclass


@dataclass
class Position:
    """Class to represent a position."""
    quantity: float
    avg_price: float
