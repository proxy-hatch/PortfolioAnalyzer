import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from lib.model.enum.account_category import AccountCategory
from lib.model.enum.account_name import AccountName
from lib.questrade.questrade import QuestradeInterface

# Sample data for testing (updated to include negative values)
# SAMPLE_POSITIONS_RRSP = [
#     {
#         'symbol': 'BRK.B',
#         'openQuantity': 26,
#         'currentMarketValue': 12185.42,
#         'currentPrice': 468.67,
#         'averageEntryPrice': 457.255385,
#         'openPnl': 296.779990,
#         'totalCost': 11888.640010
#     },
#     {
#         'symbol': 'ETN',
#         'openQuantity': 23,
#         'currentMarketValue': 7508.12,
#         'currentPrice': 326.44,
#         'averageEntryPrice': 354.143478,
#         'openPnl': -637.179994,
#         'totalCost': 8145.299994,
#     }
# ]
#
# SAMPLE_POSITIONS_TFSA = [
#     {
#         'symbol': 'MSFT',
#         'openQuantity': 26,
#         'currentMarketValue': 10791.56,
#         'currentPrice': 415.06,
#         'averageEntryPrice': 421.256538,
#         'openPnl': -161.109988,
#         'totalCost': 10952.669988,
#     },
#     {
#         'symbol': 'AAPL',
#         'openQuantity': 61,
#         'currentMarketValue': 14396.00,
#         'currentPrice': 236.00,
#         'averageEntryPrice': 222.349508,
#         'openPnl': 832.680012,
#         'totalCost': 13563.319988,
#     }
# ]

SAMPLE_POSITIONS_MARGIN = [
    {
        'Symbol': 'VOO',
        'OpenQuantity': 55,
        'CurrentMarketValue': 30433.15,
        'CurrentPrice': 553.33,
        'AverageEntryPrice': 533.548182,
        'OpenPnl': 1087.99999,
        'TotalCost': 29345.15001,
    }
]


@pytest.fixture
def mock_questrade_interface():
    with patch('lib.questrade.questrade.Questrade') as mock_questrade:
        # Mock instance
        mock_instance = mock_questrade.return_value
        mock_instance.refresh_access_token.return_value = None

        # Create the QuestradeInterface and mock its _get_holdings_by_account method
        interface = QuestradeInterface()
        interface.client = mock_instance
        interface._get_holdings_by_account = MagicMock(return_value=pd.DataFrame(SAMPLE_POSITIONS_MARGIN))

        yield interface


def test_get_holdings(mock_questrade_interface):
    # Call the method under test
    margin_df = mock_questrade_interface.get_holdings(AccountCategory.MARGIN)

    assert isinstance(margin_df, pd.DataFrame)
    assert set(margin_df.columns) == {'Symbol', 'OpenQuantity', 'CurrentMarketValue', 'CurrentPrice',
                                      'AverageEntryPrice', 'OpenPnl', 'TotalCost'}
    assert len(margin_df) == 1  # Only one position in the Margin account

    voo_row = margin_df[margin_df['Symbol'] == 'VOO'].iloc[0]
    assert voo_row['OpenQuantity'] == 55
    assert voo_row['CurrentMarketValue'] == 30433.15
    assert voo_row['OpenPnl'] == 1087.99999
    assert voo_row['TotalCost'] == 29345.15001
    assert voo_row['AverageEntryPrice'] == 533.548182

# TODO: add test for merging TFSA and RRSP positions