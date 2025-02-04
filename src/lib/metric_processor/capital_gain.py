import datetime
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
    class RealizedGainResult:
        total_realized: float
        daily_realized: pd.DataFrame  # Date, Realized Gain, Realized Loss
        daily_realized_symbols: pd.DataFrame  # Date, Symbol, Realized (represented as a positive number for gain, negative for loss)

    def process(self,
                txn_df: pd.DataFrame,
                start_date: pd.Timestamp,
                end_date: pd.Timestamp,
                # holdings_df: pd.DataFrame,
                baseline_df: pd.DataFrame,
                baseline_date: datetime.date
                ) -> RealizedGainResult:
        """
        Process the DataFrame to calculate
        1. the total realized gain for the given date range.
        2. the daily realized gain and loss for each day in the date range.

        :param baseline_date:
        :param baseline_df:
        :param txn_df:
        :param start_date:
        :param end_date:
        :return: RealizedGainData
        """
        positions: Dict[str, Position] = {}
        for _, row in baseline_df.iterrows():
            symbol = row['Symbol']
            positions[symbol] = Position(quantity=row['Quantity'], avg_price=row['AverageCost'])

        # init dataframe
        daily_realized = pd.DataFrame(columns=['Date', 'Realized Gain', 'Realized Loss'])
        daily_realized['Date'] = pd.date_range(start=start_date, end=end_date)
        daily_realized['Realized Gain'] = 0.00
        daily_realized['Realized Loss'] = 0.00
        daily_realized_symbols = pd.DataFrame(columns=['Date', 'Symbol', 'Realized'])
        daily_realized_symbols['Realized'] = daily_realized_symbols['Realized'].astype(float)

        trades = txn_df[txn_df['Activity Type'] == 'Trades']

        before_trades = trades[(trades['Date'] > baseline_date)
                               & (trades['Date'] < start_date)]
        during_trades = trades[(trades['Date'] >= start_date) & (trades['Date'] <= end_date)]

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
                    continue

                position = positions[symbol]
                if position.quantity < quantity:
                    self.logger.error(f"Attempting to sell more shares than available for {symbol} on row {i}.")
                    continue

                # Reduce the position
                positions[symbol].quantity -= quantity

        total_realized = 0.0
        for i, row in during_trades.iterrows():
            symbol, quantity, price, commission, action = astuple(self._get_row_data(row))

            if row['Action'] == 'Sell':
                if symbol not in positions:
                    self.logger.error(f"Sell transaction found for symbol {symbol} with no prior holdings on row {i}.")
                    continue

                position = positions[symbol]
                if position.quantity < quantity:
                    self.logger.error(f"Attempting to sell more shares than available for {symbol} on row {i}.")
                    continue

                # Calculate realized gain (subtract commission from proceeds)
                proceeds = (price * quantity) - commission
                cost_basis = position.avg_price * quantity
                realized = proceeds - cost_basis
                # Reduce the position
                positions[symbol].quantity -= quantity

                if realized > 0:
                    daily_realized.loc[
                        daily_realized['Date'] == row['Date'], 'Realized Gain'] += realized
                else:
                    daily_realized.loc[
                        daily_realized['Date'] == row['Date'], 'Realized Loss'] -= realized

                daily_realized_symbols = pd.concat([daily_realized_symbols, pd.DataFrame({
                    'Date': [row['Date']],
                    'Symbol': [symbol],
                    'Realized': [realized]
                })])

                total_realized += realized

            elif row['Action'] == 'Buy':
                total_cost = quantity * price + commission
                if symbol not in positions:
                    positions[symbol] = Position(quantity=quantity, avg_price=total_cost / quantity)
                else:
                    position = positions[symbol]
                    total_quantity = position.quantity + quantity
                    new_avg_price = (position.avg_price * position.quantity + total_cost) / total_quantity
                    positions[symbol] = Position(quantity=total_quantity, avg_price=new_avg_price)

        return self.RealizedGainResult(total_realized=total_realized,
                                       daily_realized=daily_realized,
                                       daily_realized_symbols=daily_realized_symbols)

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
