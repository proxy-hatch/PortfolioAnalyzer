import pandas as pd
from datetime import datetime

import pytest
from lib.metric_processor.capital_gain import CapitalGainProcessor
from pandas._testing import assert_frame_equal


def test_capital_gain_processor():
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
    processor = CapitalGainProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process_metrics(df, start_date, end_date)

    # Assert results
    assert result.total_realized == 240  # (150-(100*10+10)/10)*5 - 5 = 240
    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0] * len(date_range)
    expected_df = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    expected_df.loc[expected_df['Date'] == pd.Timestamp('2024-01-02'), 'Realized Gain'] = 240
    assert_frame_equal(result.daily_realized, expected_df)


def test_capital_gain_processor_no_sell():
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
    processor = CapitalGainProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process_metrics(df, start_date, end_date)

    # Assert results
    assert result.total_realized == 0  # No sell transactions, so no realized gain
    print(result.daily_realized)
    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0] * len(date_range)
    expected_df = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    assert_frame_equal(result.daily_realized, expected_df)


def test_capital_gain_processor_sell_to_negative_should_raise_value_error():
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
    processor = CapitalGainProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # assert
    with pytest.raises(ValueError, match='Attempting to sell more shares than available for*'):
        processor.process_metrics(df, start_date, end_date)


def test_capital_gain_processor_sell_without_bought():
    data = {
        'Date': ['2024-01-01', '2024-01-02'],
        'Activity Type': ['Trades', 'Trades'],
        'Symbol': ['AAPL', 'TSLA'],
        'Quantity': [-5, -5],
        'Price': [100, 200],
        'Commission': [-10, -5],
        'Action': ['Sell', 'Sell']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # assert
    with pytest.raises(ValueError, match='Sell transaction found for symbol*'):
        processor.process_metrics(df, start_date, end_date)


def test_capital_gain_processor_before_trades_should_affect_cumulative_position():
    data = {
        'Date': ['2023-11-01', '2023-12-01', '2024-01-01', '2024-01-02'],
        'Activity Type': ['Trades', 'Trades', 'Trades', 'Trades'],
        'Symbol': ['AAPL', 'AAPL', 'AAPL', 'AAPL'],
        'Quantity': [100, -100, 10, -5],
        'Price': [50, 1000, 100, 150],
        'Commission': [-12, -15, -10, -5],
        'Action': ['Buy', 'Sell', 'Buy', 'Sell']
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # Initialize processor
    processor = CapitalGainProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process_metrics(df, start_date, end_date)

    # Assert results
    assert result.total_realized == 240
    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0] * len(date_range)
    expected_df = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    expected_df.loc[expected_df['Date'] == pd.Timestamp('2024-01-02'), 'Realized Gain'] = 240
    assert_frame_equal(result.daily_realized, expected_df)


def test_capital_gain_processor_after_trades_should_not_affect_cap_gain():
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
    processor = CapitalGainProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 1, 2)

    # Process data
    result = processor.process_metrics(df, start_date, end_date)

    # Assert results
    assert result.total_realized == 240
    date_range = pd.date_range(start=start_date, end=end_date)
    all_zeros = [0] * len(date_range)
    expected_df = pd.DataFrame({
        'Date': date_range,
        'Realized Gain': all_zeros,
        'Realized Loss': all_zeros
    })
    expected_df.loc[expected_df['Date'] == pd.Timestamp('2024-01-02'), 'Realized Gain'] = 240
    assert_frame_equal(result.daily_realized, expected_df)
