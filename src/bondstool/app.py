import numpy as np
import pandas as pd

from bondstool.analysis.plot import (
    make_base_monthly_payments_fig,
    plot_potential_payments,
)
from bondstool.analysis.utils import (
    calc_potential_payments,
    fill_missing_months,
    payments_by_month,
)
from bondstool.data.auction import (
    filter_trading_bonds,
    get_auction_xml,
    get_doc_url_date,
    parse_xml_isins,
)
from bondstool.data.bag import merge_bonds_info, read_bag_info
from bondstool.data.bonds import (
    get_bonds_info,
    normalize_payments,
    create_payments_table,
)
from dash import Dash, Input, Output, callback, dcc, html, dash_table

raw_bonds = get_bonds_info()
bonds = normalize_payments(raw_bonds)

bag = read_bag_info()
bag = merge_bonds_info(bag, bonds)

doc_url, auc_date = get_doc_url_date()

isin_df = parse_xml_isins(get_auction_xml(doc_url))

trading_bonds = filter_trading_bonds(isin_df, bonds)

monthly_bag = payments_by_month(bag)
monthly_bag = fill_missing_months(monthly_bag)

base_fig = make_base_monthly_payments_fig(monthly_bag)


app = Dash(__name__)

SLIDER_STEPS = np.arange(0, 5000, 200)


def create_slider(id):

    return html.Div(
        [
            html.Label(id, htmlFor=id),
            dcc.Slider(
                SLIDER_STEPS.min(),
                SLIDER_STEPS.max(),
                step=None,
                value=SLIDER_STEPS.min(),
                marks={str(val): str(val) for val in SLIDER_STEPS},
                id=id,
            ),
        ]
    )


sliders = [create_slider(isin) for isin in isin_df["ISIN"].values]

app.layout = html.Div(
    [
        html.Div(
            [
                html.H1(auc_date, style={"text-align": "center", "margin": "1px 0"}),
            ],
            style={"display": "flex", "justify-content": "center"},
        ),
        dcc.Graph(id="graph-with-slider"),
        *sliders,
        dcc.Input(id="search-input", type="text", placeholder="Enter ISIN"),
        html.Button("▼", id="dropdown-button"),
        dcc.Dropdown(
            id="dropdown",
            options=[{"label": isin, "value": isin} for isin in raw_bonds["ISIN"]],
            placeholder="Select an ISIN",
            style={"display": "none"},
        ),
        html.Div(id="search-output"),
        html.H2("Bag Data", style={"text-align": "center", "margin-top": "20px"}),
        html.Div(
            dash_table.DataTable(
                id="bag-table",
                columns=[{"name": col, "id": col} for col in bag.columns],
                data=bag.to_dict("records"),
            ),
            style={"margin-top": "10px"},
        ),
    ]
)


sliders_input = [Input(isin, "value") for isin in isin_df["ISIN"].values]


@callback(Output("graph-with-slider", "figure"), *sliders_input)
def update_figure(*amounts):

    potential_payments = calc_potential_payments(
        trading_bonds, amounts, monthly_bag, isin_df
    )

    fig = plot_potential_payments(base_fig, potential_payments)

    fig.update_layout(transition_duration=500)

    return fig


@callback(
    Output("search-output", "children"),
    [Input("search-input", "value"), Input("dropdown", "value")],
)
def update_search_output(input_value, selected_isin):
    if input_value:
        search_value = input_value
    elif selected_isin:
        search_value = selected_isin
    else:
        return None

    bond = raw_bonds[raw_bonds["ISIN"].str.contains(search_value, case=False)]

    if bond.empty:
        return f"No matching records for '{search_value}'."

    payment_dfs = bond.apply(create_payments_table, axis=1)

    df = pd.concat(payment_dfs.tolist(), ignore_index=True)
    df = df.drop("ISIN", axis=1)

    combined_df = pd.concat([bond, df], axis=1)

    combined_df = combined_df.drop("payments", axis=1)

    table_data = combined_df.to_dict("records")
    table_columns = [{"name": col, "id": col} for col in combined_df.columns]

    table = dash_table.DataTable(
        id="combined-table",
        columns=table_columns,
        data=table_data,
    )

    return table


@callback(Output("dropdown", "style"), [Input("dropdown-button", "n_clicks")])
def toggle_dropdown(n_clicks):
    if n_clicks and n_clicks % 2 != 0:
        return {"display": "block"}
    return {"display": "none"}


if __name__ == "__main__":
    app.run(debug=True)
