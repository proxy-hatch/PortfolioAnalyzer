import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from lib.model.enum.account_category import AccountCategory
from lib.model.enum.account_name import AccountName
from lib.questrade.questrade import QuestradeInterface

# Sample data for testing (updated to include negative values)
SAMPLE_POSITIONS_RRSP = [
    {
        'symbol': 'BRK.B',
        'openQuantity': 26,
        'currentMarketValue': 12185.42,
        'currentPrice': 468.67,
        'averageEntryPrice': 457.255385,
        'openPnl': 296.779990,
        'totalCost': 11888.640010
    },
    {
        'symbol': 'ETN',
        'openQuantity': 23,
        'currentMarketValue': 7508.12,
        'currentPrice': 326.44,
        'averageEntryPrice': 354.143478,
        'openPnl': -637.179994,
        'totalCost': 8145.299994,
    }
]

SAMPLE_POSITIONS_TFSA = [
    {
        'symbol': 'MSFT',
        'openQuantity': 26,
        'currentMarketValue': 10791.56,
        'currentPrice': 415.06,
        'averageEntryPrice': 421.256538,
        'openPnl': -161.109988,
        'totalCost': 10952.669988,
    },
    {
        'symbol': 'AAPL',
        'openQuantity': 61,
        'currentMarketValue': 14396.00,
        'currentPrice': 236.00,
        'averageEntryPrice': 222.349508,
        'openPnl': 832.680012,
        'totalCost': 13563.319988,
    }
]

SAMPLE_POSITIONS_MARGIN = [
    {
        'symbol': 'VOO',
        'openQuantity': 55,
        'currentMarketValue': 30433.15,
        'currentPrice': 553.33,
        'averageEntryPrice': 533.548182,
        'openPnl': 1087.99999,
        'totalCost': 29345.15001,
    }
]

# Mocking account IDs
MOCK_ACCOUNT_HOLDINGS = {
    AccountName.RRSP: pd.DataFrame(SAMPLE_POSITIONS_RRSP),
    AccountName.TFSA: pd.DataFrame(SAMPLE_POSITIONS_TFSA),
    AccountName.MARGIN: pd.DataFrame(SAMPLE_POSITIONS_MARGIN),
}



@pytest.fixture
def mock_questrade_interface():
    with patch('lib.questrade.questrade.Questrade') as mock_questrade:
        # Mock instance
        mock_instance = mock_questrade.return_value
        mock_instance.refresh_access_token.return_value = None
        # mock_instance._get_holdings_by_account.side_effect = lambda account_id: MOCK_ACCOUNT_HOLDINGS.get(account_id, pd.DataFrame())

        # Create the QuestradeInterface and mock its _get_holdings_by_account method
        interface = QuestradeInterface()
        interface.client = mock_instance
        interface._get_holdings_by_account = MagicMock(return_value=MOCK_ACCOUNT_HOLDINGS)

        yield interface

#
# @pytest.fixture
# def questrade_interface():
#     with patch('lib.questrade.questrade.Questrade') as mock_questrade:
#         mock_instance = mock_questrade.return_value
#         mock_instance.refresh_access_token.return_value = None
#
#         interface = QuestradeInterface()
#         interface.client = mock_instance  # Ensure the interface client is patched properly
#         interface.client.get_account_positions = MagicMock(side_effect={
#             AccountName.MARGIN: SAMPLE_POSITIONS_MARGIN,
#             AccountName.TFSA: SAMPLE_POSITIONS_TFSA,
#             AccountName.RRSP: SAMPLE_POSITIONS_RRSP
#         })
#         yield interface


def test_get_holdings(mock_questrade_interface):
    # Call the method under test
    holdings = mock_questrade_interface.get_holdings()

    # Assert that the returned dictionary contains the correct keys
    assert AccountCategory.TFSA_RRSP in holdings
    assert AccountCategory.MARGIN in holdings

    # Assert that the TFSA_RRSP DataFrame is correctly merged and deduplicated
    tfsa_rrsp_df = holdings[AccountCategory.TFSA_RRSP]
    print(tfsa_rrsp_df.head(50))
    assert isinstance(tfsa_rrsp_df, pd.DataFrame)
    assert set(tfsa_rrsp_df.columns) == {'symbol', 'openQuantity', 'currentMarketValue', 'currentPrice',
                                         'averageEntryPrice', 'openPnl', 'totalCost'}
    assert len(tfsa_rrsp_df) == 4  # 2 from RRSP + 2 from TFSA (no duplicates in this sample)

    # Assert that the MARGIN DataFrame is correctly structured
    margin_df = holdings[AccountCategory.MARGIN]
    assert isinstance(margin_df, pd.DataFrame)
    assert set(margin_df.columns) == {'symbol', 'openQuantity', 'currentMarketValue', 'currentPrice',
                                      'averageEntryPrice', 'openPnl', 'totalCost'}
    assert len(margin_df) == 1  # Only one position in the Margin account

    # Assert that the averageEntryPrice is correctly calculated
    for _, row in tfsa_rrsp_df.iterrows():
        assert row['averageEntryPrice'] == row['totalCost'] / row['openQuantity']

    # Assert specific values in the TFSA_RRSP DataFrame
    brkb_row = tfsa_rrsp_df[tfsa_rrsp_df['symbol'] == 'BRK.B'].iloc[0]
    assert brkb_row['openQuantity'] == 26
    assert brkb_row['currentMarketValue'] == 12185.42
    assert brkb_row['openPnl'] == 296.779990
    assert brkb_row['totalCost'] == 11888.640010
    assert brkb_row['averageEntryPrice'] == 457.255385

    etn_row = tfsa_rrsp_df[tfsa_rrsp_df['symbol'] == 'ETN'].iloc[0]
    assert etn_row['openQuantity'] == 23
    assert etn_row['currentMarketValue'] == 7508.12
    assert etn_row['openPnl'] == -637.179994
    assert etn_row['totalCost'] == 8145.299994
    assert etn_row['averageEntryPrice'] == 354.143478

    # Assert specific values in the Margin DataFrame
    voo_row = margin_df[margin_df['symbol'] == 'VOO'].iloc[0]
    assert voo_row['openQuantity'] == 55
    assert voo_row['currentMarketValue'] == 30433.15
    assert voo_row['openPnl'] == 1087.99999
    assert voo_row['totalCost'] == 29345.15001
    assert voo_row['averageEntryPrice'] == 533.548182


def test_get_holdings_with_duplicates(mock_questrade_interface):
    # Modify the sample data to include duplicates
    duplicate_positions_tfsa = SAMPLE_POSITIONS_TFSA + [
        {
            'symbol': 'BRK.B',
            'openQuantity': 10,
            'currentMarketValue': 4686.70,
            'currentPrice': 468.67,
            'averageEntryPrice': 457.255385,
            'openPnl': 100.00,
            'totalCost': 4572.55,
        }
    ]

    mock_questrade_interface._get_holdings_by_account = MagicMock(return_value={
            AccountName.RRSP: pd.DataFrame(SAMPLE_POSITIONS_RRSP),
            AccountName.TFSA: pd.DataFrame(duplicate_positions_tfsa),
            AccountName.MARGIN: pd.DataFrame(SAMPLE_POSITIONS_MARGIN),
        })

    # Call the method under test
    holdings = mock_questrade_interface.get_holdings()

    # Assert that the TFSA_RRSP DataFrame is correctly merged and deduplicated
    tfsa_rrsp_df = holdings[AccountCategory.TFSA_RRSP]
    brkb_row = tfsa_rrsp_df[tfsa_rrsp_df['symbol'] == 'BRK.B'].iloc[0]
    assert brkb_row['openQuantity'] == 36  # 26 + 10
    assert brkb_row['currentMarketValue'] == 12185.42 + 4686.70
    assert brkb_row['openPnl'] == 296.779990 + 100.00
    assert brkb_row['totalCost'] == 11888.640010 + 4572.55
    assert brkb_row['averageEntryPrice'] == (11888.640010 + 4572.55) / (26 + 10)
