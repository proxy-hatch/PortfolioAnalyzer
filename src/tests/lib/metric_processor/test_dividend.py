import pytest
import pandas as pd
from datetime import datetime
from lib.metric_processor.dividend import DividendProcessor


def test_dividend_processor():
    # Create sample data
    data = {
        'Date': ['2024-01-01 12:00:00 PM', '2024-01-02 12:00:00 PM'],
        'Activity Type': ['Dividends', 'Dividends'],
        'Net Amount': [100, 200]
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %I:%M:%S %p')

    # Initialize processor
    processor = DividendProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process_metrics(df, start_date, end_date)

    # Assert results
    assert 'Total Dividends' in result
    assert result['Total Dividends'] == 300  # 100 + 200 = 300


def test_dividend_processor_no_dividends():
    # Create sample data with no dividends
    data = {
        'Date': ['2024-01-01 12:00:00 PM'],
        'Activity Type': ['Trades'],
        'Net Amount': [100]
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %I:%M:%S %p')

    # Initialize processor
    processor = DividendProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process_metrics(df, start_date, end_date)

    # Assert results
    assert 'Total Dividends' in result
    assert result['Total Dividends'] == 0  # No dividends in the data


def test_dividend_outside_of_date_range_should_be_ignored():
    # Create sample data
    data = {
        'Date': ['2024-01-01 12:00:00 PM', '2024-01-02 12:00:00 PM'],
        'Activity Type': ['Dividends', 'Dividends'],
        'Net Amount': [100, 200]
    }
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d %I:%M:%S %p')

    # Initialize processor
    processor = DividendProcessor()

    # Define start and end dates
    start_date = datetime(2024, 1, 2)
    end_date = datetime(2024, 12, 31)

    # Process data
    result = processor.process_metrics(df, start_date, end_date)

    # Assert results
    assert 'Total Dividends' in result
    assert result['Total Dividends'] == 200  # Only the second dividend should be included
