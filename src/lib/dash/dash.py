from datetime import datetime
from typing import Dict

import pandas as pd
from dash import Dash, html, dcc, Output, Input
import plotly.express as px
from dash.dash_table import DataTable
from dash_table import FormatTemplate

from lib.model.enum.account_category import AccountCategory

from lib.metric_processor.processor import process_metrics

from lib.metric_processor.processor import MetricsResult

from lib.logger.logger import get_logger
from lib.questrade.questrade import QuestradeInterface

TXN_FILEPATH = '../data/all_txns.csv'
STATEMENTS_FILEPATH = '../data/statements'
BASELINE_DATE = '2023-12-31'

# Global variables to store analysis result
analysis_result: Dict[AccountCategory, MetricsResult] = {}


def create_dash_app(questrade_client: QuestradeInterface) -> Dash:
    """
    Create a Dash app to display the analysis result.

    :param txn_df: DataFrame containing transaction data.
    :param baseline_df: DataFrame containing holdings data.
    :param baseline_date: The baseline date for the holdings data.
    :return: Dash app
    """
    global analysis_result, analysis_updated
    logger = get_logger()

    app = Dash(__name__)

    # Create dropdown options for account categories
    account_options = [{'label': account.name, 'value': account.name} for account in AccountCategory]

    app.layout = html.Div([
        dcc.Dropdown(
            id='account-category-dropdown',
            options=account_options,
            value=AccountCategory.TFSA_RRSP.name  # Default value
        ),
        dcc.DatePickerRange(
            id='date-range-picker',
            start_date='2024-01-01',
            end_date='2024-12-31'
        ),
        # Hidden div to trigger upon analysis result update
        html.Div(id='analysis_result_updated', style={'display': 'none'}),
        html.Div(id='summary'),
        dcc.Graph(id='monthly-bar-chart'),
        html.Div(id='daily-details')
    ])

    @app.callback(
        Output('analysis_result_updated', 'children'),
        [Input('date-range-picker', 'start_date'),
         Input('date-range-picker', 'end_date'),
         Input('account-category-dropdown', 'value'),
         ]
    )
    def update_analysis_result(start_date, end_date, selected_account):
        logger.info(f"Updating analysis result with start date: {start_date}, end date: {end_date}, "
                    f"selected account: {selected_account}")
        account_category = AccountCategory.categorize(selected_account)
        start_date  = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        txn_df = questrade_client.get_account_activities(account_category, start_date, end_date)
        holdings_df = questrade_client.get_holdings()[account_category]

        global analysis_result
        analysis_result = process_metrics(txn_df=txn_df, holdings_df=holdings_df, start_date=start_date,
                                          end_date=end_date)
        logger.info(f"Analysis result updated.")
        return

# TODO: update
    @app.callback(
        [Output('summary', 'children'),
         Output('monthly-bar-chart', 'figure')],
        [Input('account-category-dropdown', 'value'),
         Input('analysis_result_updated', 'children')]  # Trigger on analysis result update
    )
    def update_dashboard(selected_account, _):
        global analysis_result

        account_category = AccountCategory[selected_account]
        result = analysis_result[account_category]

        # Create summary table
        summary_table = DataTable(
            data=[result.summary],
            columns=[{"name": i, "id": i, "type": "numeric", "format": FormatTemplate.money(2)} for i in
                     result.summary],
            style_table={'overflowX': 'auto'},
            style_cell={'textAlign': 'left'},
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            }
        )

        # Aggregate data by month
        daily_realized = result.daily_realized
        daily_realized['Month'] = daily_realized['Date'].dt.to_period('M')
        monthly_realized = daily_realized.groupby('Month').agg({
            'Realized Gain': 'sum',
            'Realized Loss': 'sum'
        }).reset_index()
        monthly_realized['Month'] = monthly_realized['Month'].dt.to_timestamp()

        # Create bar chart
        fig = px.bar(monthly_realized, x='Month', y=['Realized Gain', 'Realized Loss'],
                     barmode='group', title='Monthly Realized Gain/Loss')
        fig.update_layout(xaxis=dict(dtick="M1"))  # show label for every month

        return summary_table, fig

    @app.callback(
        Output('daily-details', 'children'),
        [Input('monthly-bar-chart', 'clickData'),
         Input('account-category-dropdown', 'value'),
         Input('analysis_result_updated', 'children')]
    )
    def display_daily_details(click_data, selected_account, _):
        global analysis_result

        if click_data is None:
            return html.Div()

        account_category = AccountCategory[selected_account]
        result = analysis_result[account_category]
        daily_realized_symbols = result.daily_realized_symbols

        month = click_data['points'][0]['x']
        is_gain = click_data['points'][0]['curveNumber'] == 0

        month_str = pd.to_datetime(month).strftime('%Y-%m')
        daily_details = daily_realized_symbols[
            (daily_realized_symbols['Date'].dt.strftime('%Y-%m') == month_str) &
            (daily_realized_symbols['Realized'] > 0 if is_gain else daily_realized_symbols['Realized'] < 0)
            ]

        return html.Ul([
            html.Li(
                children=[
                    html.Span(f"{row['Date'].date()}",
                              style={'font-weight': 'bold', 'display': 'inline-block', 'width': '100px'}),
                    html.Span(f"[{row['Symbol']}]",
                              style={'font-weight': 'bold', 'color': 'blue', 'display': 'inline-block',
                                     'width': '80px'}),
                    html.Span(
                        f"${row['Realized']:.2f}",  # Format to 2 decimal places
                        style={'color': 'green' if row['Realized'] >= 0 else 'red', 'display': 'inline-block',
                               'width': '100px'}
                    )
                ],
                style={'list-style-type': 'none'}  # Remove bullet points
            ) for _, row in daily_details.iterrows()
        ])

    return app
