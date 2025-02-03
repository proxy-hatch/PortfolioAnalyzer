import logging

import pandas as pd
from datetime import datetime

import pytest
from lib.metric_processor.capital_gain import CapitalGainProcessor
from pandas._testing import assert_frame_equal

from lib.model.enum.account_category import AccountCategory

holdings_data = {
    'Symbol': ['TSLA', 'BRK.B'],
    'Quantity': [10, 5],
    'AverageCost': [100, 150],
    'Account Category': [AccountCategory.TFSA_RRSP, AccountCategory.TFSA_RRSP]
}
holdings_df = pd.DataFrame(holdings_data)
holdings_date = datetime(2022, 1, 1)


def test_capital_gain_processor_when_no_holding():
    # Create sample data
    data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Activity Type': ['Trades', 'Trades', 'Trades'],
        'Symbol': ['AAPL', 'AAPL', 'AAPL'],
        'Quantity': [10, -5, 5],
        'Price': [100, 150, 200],
        'Commission': [-10, -5, -5],
        'Action': ['Buy', 'Sell', 'Buy']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor(holdings_df, holdings_date)

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process(txn_df=df, start_date=start_date, end_date=end_date,
                               account_category=AccountCategory.TFSA_RRSP)

    # Assert results
    assert result.total_realized == 240  # (150-(100*10+10)/10)*5 - 5 = 240

    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0.0] * len(date_range)
    expected_daily_realized = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    expected_daily_realized.loc[expected_daily_realized['Date'] == pd.Timestamp('2024-01-02'), 'Realized Gain'] = 240
    assert_frame_equal(result.daily_realized, expected_daily_realized)

    expected_daily_realized_symbols = pd.DataFrame({
        'Date': [pd.Timestamp('2024-01-02')],
        'Symbol': ['AAPL'],
        'Realized': [240.0]
    })
    assert_frame_equal(result.daily_realized_symbols, expected_daily_realized_symbols)


def test_capital_gain_processor_when_no_holding_no_sell():
    # Create sample data with no sell transactions
    data = {
        'Date': ['2024-01-01', '2024-01-02'],
        'Activity Type': ['Trades', 'Trades'],
        'Symbol': ['AAPL', 'AAPL'],
        'Quantity': [10, 5],
        'Price': [100, 200],
        'Commission': [-10, -5],
        'Action': ['Buy', 'Buy']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor(holdings_df, holdings_date)

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process(txn_df=df, start_date=start_date, end_date=end_date,
                               account_category=AccountCategory.TFSA_RRSP)

    # Assert results
    assert result.total_realized == 0  # No sell transactions, so no realized gain

    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0.0] * len(date_range)
    expected_df = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    assert_frame_equal(result.daily_realized, expected_df)

    expected_df = pd.DataFrame(columns=['Date', 'Symbol', 'Realized'])
    expected_df['Realized'] = expected_df['Realized'].astype(float)
    assert_frame_equal(result.daily_realized_symbols, expected_df)


def test_capital_gain_processor_when_no_holding_sell_to_negative_should_log_error(caplog):
    data = {
        'Date': ['2024-01-01', '2024-01-02'],
        'Activity Type': ['Trades', 'Trades'],
        'Symbol': ['AAPL', 'AAPL'],
        'Quantity': [10, -15],
        'Price': [100, 200],
        'Commission': [-10, -5],
        'Action': ['Buy', 'Sell']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor(holdings_df, holdings_date)

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    with caplog.at_level(logging.ERROR):
        processor.process(txn_df=df, start_date=start_date, end_date=end_date, account_category=AccountCategory.TFSA_RRSP)

    assert any("Attempting to sell more shares than available for" in message for message in caplog.messages)


def test_capital_gain_processor_when_no_holding_sell_without_bought_should_log_error(caplog):
    data = {
        'Date': ['2024-01-01', '2024-01-02'],
        'Activity Type': ['Trades', 'Trades'],
        'Symbol': ['AAPL', 'ZIM'],
        'Quantity': [-5, -5],
        'Price': [100, 200],
        'Commission': [-10, -5],
        'Action': ['Sell', 'Sell']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor(holdings_df, holdings_date)

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    with caplog.at_level(logging.ERROR):
        processor.process(txn_df=df, start_date=start_date, end_date=end_date, account_category=AccountCategory.TFSA_RRSP)

    assert any("Sell transaction found for symbol" in message for message in caplog.messages)


def test_capital_gain_processor_when_no_holding_before_trades_should_affect_cumulative_position():
    data = {
        'Date': ['2023-11-01', '2023-12-01', '2024-01-01', '2024-01-02'],
        'Activity Type': ['Trades', 'Trades', 'Trades', 'Trades'],
        'Symbol': ['AAPL', 'AAPL', 'AAPL', 'AAPL'],
        'Quantity': [100, -95, 5, -5],
        'Price': [100, 1000, 100, 150],
        'Commission': [0, -15, -10, -5],
        'Action': ['Buy', 'Sell', 'Buy', 'Sell']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor(holdings_df, holdings_date)

    # Define start and end dates
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process(txn_df=df, start_date=start_date, end_date=end_date,
                               account_category=AccountCategory.TFSA_RRSP)

    # Assert results
    assert result.total_realized == 240
    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0.0] * len(date_range)
    expected_df = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    expected_df.loc[expected_df['Date'] == pd.Timestamp('2024-01-02'), 'Realized Gain'] = 240.0
    assert_frame_equal(result.daily_realized, expected_df)


def test_capital_gain_processor_when_no_holding_after_trades_should_not_affect_cap_gain():
    data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
        'Activity Type': ['Trades', 'Trades', 'Trades', 'AAPL'],
        'Symbol': ['AAPL', 'AAPL', 'AAPL', 'AAPL'],
        'Quantity': [10, -5, 5, -10],
        'Price': [100, 150, 200, 1000],
        'Commission': [-10, -5, -5, -5],
        'Action': ['Buy', 'Sell', 'Buy', 'Sell']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor(holdings_df, holdings_date)

    # Define start and end dates
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 1, 2)

    # Process data
    result = processor.process(txn_df=df, start_date=start_date, end_date=end_date,
                               account_category=AccountCategory.TFSA_RRSP)

    # Assert results
    assert result.total_realized == 240
    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0.0] * len(date_range)
    expected_df = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    expected_df.loc[expected_df['Date'] == pd.Timestamp('2024-01-02'), 'Realized Gain'] = 240
    assert_frame_equal(result.daily_realized, expected_df)


#
def test_capital_gain_processor_when_holding_should_affect_cap_gain():
    # Create sample data
    data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03'],
        'Activity Type': ['Trades', 'Trades', 'Trades'],
        'Symbol': ['AAPL', 'TSLA', 'AAPL'],
        'Quantity': [10, -5, 5],
        'Price': [100, 150, 200],
        'Commission': [-10, -5, -5],
        'Action': ['Buy', 'Sell', 'Buy']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor(holdings_df, holdings_date)

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process(txn_df=df, start_date=start_date, end_date=end_date,
                               account_category=AccountCategory.TFSA_RRSP)

    # Assert results
    assert result.total_realized == 245  # (150-(100*10+0)/10)*5 - 5 = 245

    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0.0] * len(date_range)
    expected_daily_realized = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    expected_daily_realized.loc[expected_daily_realized['Date'] == pd.Timestamp('2024-01-02'), 'Realized Gain'] = 245
    assert_frame_equal(result.daily_realized, expected_daily_realized)

    expected_daily_realized_symbols = pd.DataFrame({
        'Date': [pd.Timestamp('2024-01-02')],
        'Symbol': ['TSLA'],
        'Realized': [245.0]
    })
    assert_frame_equal(result.daily_realized_symbols, expected_daily_realized_symbols)
#
# def test_capital_gain_processor_when_holding_should_affect_before_trade():
