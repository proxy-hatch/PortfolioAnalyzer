from dataclasses import dataclass, astuple
from typing import Dict, TypedDict

import pandas as pd

from lib.metric_processor.base import BaseProcessor

from lib.model.position import Position

from lib.model.enum.action import Action


class CapitalGainProcessor(BaseProcessor):
    def __init__(self):
        super().__init__()

    @dataclass
    class RealizedGainData:
        total_realized_gain: float
        daily_realized_gain: pd.DataFrame

    def process(self, df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> RealizedGainData:
        """
        Process the DataFrame to calculate
        1. the total realized gain for the given date range.
        2. the daily realized gain and loss for each day in the date range.

        :param df:
        :param start_date:
        :param end_date:
        :return: RealizedGainData
        """
        realized_gain = 0
        positions: Dict[str, Position] = {}

        # init dataframe
        daily_realized_gain = pd.DataFrame(columns=['Date', 'Realized Gain', 'Realized Loss'])
        daily_realized_gain['Date'] = pd.date_range(start=start_date, end=end_date)
        daily_realized_gain['Realized Gain'] = 0
        daily_realized_gain['Realized Loss'] = 0

        trades = df[df['Activity Type'] == 'Trades']

        before_trades = trades[trades['Transaction Date'] < start_date]
        during_trades = trades[(trades['Transaction Date'] >= start_date) & (trades['Transaction Date'] <= end_date)]

        # Process before_trades to establish cost basis
        for i, row in before_trades.iterrows():
            symbol, quantity, price, commission, action = astuple(self._get_row_data(row))

            if row['Action'] == 'Buy':
                total_cost = quantity * price + commission
                if symbol not in positions:
                    positions[symbol] = Position(quantity=quantity, avg_price=total_cost / quantity)
                else:
                    position = positions[symbol]
                    total_quantity = position.quantity + quantity
                    new_avg_price = (position.avg_price * position.quantity + total_cost) / total_quantity
                    positions[symbol] = Position(quantity=total_quantity, avg_price=new_avg_price)

            elif row['Action'] == 'Sell':
                if symbol not in positions:
                    self.logger.error(f"Sell transaction found for symbol {symbol} with no prior holdings on row {i}.")
                    raise ValueError(f"Sell transaction found for symbol {symbol} with no prior holdings.")
                position = positions[symbol]
                if position.quantity < quantity:
                    raise ValueError(f"Attempting to sell more shares than available for {symbol}.")
                # Reduce the position
                positions[symbol].quantity -= quantity

        for i, row in during_trades.iterrows():
            symbol, quantity, price, commission, action = astuple(self._get_row_data(row))

            if row['Action'] == 'Sell':
                if symbol not in positions:
                    self.logger.error(f"Sell transaction found for symbol {symbol} with no prior holdings on row {i}.")
                    raise ValueError(f"Sell transaction found for symbol {symbol} with no prior holdings.")
                position = positions[symbol]
                if position.quantity < quantity:
                    raise ValueError(f"Attempting to sell more shares than available for {symbol}.")
                # Calculate realized gain (subtract commission from proceeds)
                proceeds = (price * quantity) - commission
                cost_basis = position.avg_price * quantity
                realized_gain += proceeds - cost_basis
                # Reduce the position
                positions[symbol].quantity -= quantity

                if realized_gain > 0:
                    daily_realized_gain.loc[
                        daily_realized_gain['Date'] == row['Transaction Date'], 'Realized Gain'] = realized_gain
                else:
                    daily_realized_gain.loc[
                        daily_realized_gain['Date'] == row['Transaction Date'], 'Realized Loss'] = realized_gain

            elif row['Action'] == 'Buy':
                total_cost = quantity * price + commission
                if symbol not in positions:
                    positions[symbol] = Position(quantity=quantity, avg_price=total_cost / quantity)
                else:
                    position = positions[symbol]
                    total_quantity = position.quantity + quantity
                    new_avg_price = (position.avg_price * position.quantity + total_cost) / total_quantity
                    positions[symbol] = Position(quantity=total_quantity, avg_price=new_avg_price)

        return self.RealizedGainData(total_realized_gain=realized_gain, daily_realized_gain=daily_realized_gain)

    @dataclass
    class RowData:
        symbol: str
        quantity: int
        price: float
        commission: float
        action: Action

    def _get_row_data(self, row: pd.Series) -> RowData:
        return self.RowData(
            symbol=row['Symbol'],
            quantity=abs(row['Quantity']),
            price=row['Price'],
            commission=abs(row['Commission']),
            action=Action(row['Action'])
        )
