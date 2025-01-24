import argparse
import logging
import sys
from collections import defaultdict
from typing import Optional, List, Dict

import pandas as pd

from src.lib.model import AccountCategory, Position

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def preprocess_data(filepath: str) -> pd.DataFrame:
    """
    Preprocess the transaction data: filter by date, exclude 'DLR' transactions, and classify accounts.

    Args:
        filepath: Path to the transaction CSV file.

    Returns:
        A cleaned and sorted DataFrame.
    """
    df = pd.read_csv(filepath)

    # Convert dates to datetime
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'])

    # Exclude transactions involving 'DLR' in the description
    df = df[~df['Description'].str.contains('DLR', case=False, na=False)]

    # Classify accounts
    df['Account Category'] = df['Account Type'].apply(AccountCategory.categorize)

    # Sort transactions by date
    df = df.sort_values(by='Transaction Date').reset_index(drop=True)

    return df


def calculate_realized_gain(df: pd.DataFrame, start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
    """
    Calculate the realized gain for each account category, considering partial exits.

    Args:
        df: A DataFrame of transactions.
        start_date: Start date for the calculation.
        end_date: End date for the calculation.

    Returns:
        A summary DataFrame with realized gain details.
    """
    results = []

    # Parse dates
    start_date = pd.to_datetime(start_date) if start_date else df['Transaction Date'].min()
    end_date = pd.to_datetime(end_date) if end_date else df['Transaction Date'].max()

    for account_category in AccountCategory:
        account_data = df[df['Account Category'] == account_category.value]

        # Separate trades and dividends
        trades = account_data[account_data['Activity Type'] == 'Trades']
        dividends = account_data[account_data['Activity Type'] == 'Dividends']

        # Filter trades into before, during, and after periods
        before_trades = trades[trades['Transaction Date'] < start_date]
        during_trades = trades[(trades['Transaction Date'] >= start_date) & (trades['Transaction Date'] <= end_date)]

        # Track positions
        positions: Dict[str, List[Position]] = defaultdict(list)

        # Process before_trades to establish cost basis
        for _, row in before_trades.iterrows():
            symbol = row['Symbol']
            quantity = row['Quantity']
            price = row['Price']

            if row['Action'] == 'Buy':
                positions[symbol].append(Position(quantity=quantity, price=price))
            elif row['Action'] == 'Sell':
                remaining_to_sell = quantity
                while remaining_to_sell > 0 and positions[symbol]:
                    lot = positions[symbol][0]
                    if lot.quantity <= remaining_to_sell:
                        remaining_to_sell -= lot.quantity
                        positions[symbol].pop(0)
                    else:
                        lot.quantity -= remaining_to_sell
                        remaining_to_sell = 0

        # Calculate realized gain/loss during the period
        realized_gain = 0
        for _, row in during_trades.iterrows():
            symbol = row['Symbol']
            quantity = row['Quantity']
            price = row['Price']

            if row['Action'] == 'Sell':
                remaining_to_sell = quantity
                while remaining_to_sell > 0 and positions[symbol]:
                    lot = positions[symbol][0]
                    if lot.quantity <= remaining_to_sell:
                        realized_gain += (price - lot.price) * lot.quantity
                        remaining_to_sell -= lot.quantity
                        positions[symbol].pop(0)
                    else:
                        realized_gain += (price - lot.price) * remaining_to_sell
                        lot.quantity -= remaining_to_sell
                        remaining_to_sell = 0
            elif row['Action'] == 'Buy':
                positions[symbol].append(Position(quantity=quantity, price=price))

        # Calculate total dividends during the period
        total_dividends = dividends[
            (dividends['Transaction Date'] >= start_date) & (dividends['Transaction Date'] <= end_date)
            ]['Net Amount'].sum()

        # Append results
        results.append({
            'Account Category': account_category,
            'Realized Gain': realized_gain + total_dividends,
            'Total Dividends': total_dividends
        })

    return pd.DataFrame(results)


def main(start_date: Optional[str], end_date: Optional[str]) -> None:
    """
    Main function to calculate realized gain and benchmark.

    Args:
        start_date: Start date for the calculation.
        end_date: End date for the calculation.
        dry_run: If True, perform a dry run without making changes.
    """
    logger.info("Starting realized gain calculation.")

    file_path = 'data/20200101-20250123_txns.csv'

    # Preprocess data
    df = preprocess_data(file_path)

    # Calculate realized gain
    results = calculate_realized_gain(df, start_date, end_date)
    logger.info("Calculation completed. Results:")
    print(results)

    results.to_csv('realized_gain_results.csv', index=False)
    logger.info("Results saved to 'realized_gain_results.csv'.")


def start(args: List[str]) -> None:
    """
    Argument parser entry point.

    Args:
        args: Command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Realized Gain Calculator")
    parser.add_argument("-s", "--start-date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("-e", "--end-date", type=str, help="End date (YYYY-MM-DD)")
    args = parser.parse_args(args)

    main(start_date=args.start_date, end_date=args.end_date)


if __name__ == "__main__":
    start(sys.argv[1:])
