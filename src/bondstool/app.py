import numpy as np
import pandas as pd
from bondstool.analysis.plot import (
    make_base_monthly_payments_fig,
    plot_potential_payments,
)
from bondstool.analysis.utils import (
    calc_potential_payments,
    calculate_profitability,
    fill_missing_months,
    payments_by_month,
)
from bondstool.data.auction import (
    filter_trading_bonds,
    get_auction_xml,
    get_doc_url_date,
    parse_xml_isins,
)
from bondstool.data.bag import format_bag, merge_bonds_info, read_bag_info
from bondstool.data.bonds import (
    MAP_HEADINGS,
    get_bonds_info,
    get_recommended_bonds,
    normalize_payments,
)
from bondstool.utils import get_styleby_condition
from dash import Dash, Input, Output, callback, dash_table, dcc, html

raw_bonds = get_bonds_info()
bonds = normalize_payments(raw_bonds)
bonds = calculate_profitability(bonds)

bag = read_bag_info()
bag = merge_bonds_info(bag, bonds)

doc_url, auc_date = get_doc_url_date()

isin_df = parse_xml_isins(get_auction_xml(doc_url))

trading_bonds = filter_trading_bonds(isin_df, bonds)

formatted_bag = format_bag(bag)

monthly_bag = payments_by_month(bag)
monthly_bag = fill_missing_months(monthly_bag)

recommended_bonds = get_recommended_bonds(bonds, monthly_bag)

base_fig = make_base_monthly_payments_fig(monthly_bag)


app = Dash(__name__)

SLIDER_STEPS = np.arange(0, 5000, 200)


def create_slider(id):
    if id in recommended_bonds["ISIN"].values:
        label_style = {"color": "red"}
    else:
        label_style = {}

    return html.Div(
        [
            html.Label(id, htmlFor=id, style=label_style),
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
                html.H1(
                    "Аналітика облігацій",
                    style={
                        "text-align": "center",
                        "margin-bottom": "0.5px",
                        "font-size": "30px",
                    },
                ),
            ],
            style={"display": "flex", "justify-content": "center"},
        ),
        dcc.Graph(id="graph-with-slider"),
        html.Div(
            [
                html.H2(
                    f"Облігації доступні на аукціоні: {auc_date}",
                    style={
                        "text-align": "center",
                        "margin": "1px 0",
                        "font-size": "25px",
                    },
                ),
            ],
            style={"display": "flex", "justify-content": "center"},
        ),
        html.Div(
            [
                html.P(
                    "*Облігації червоним кольором рекомендовані",
                    style={
                        "text-align": "right",
                        "margin-top": "0.5px",
                        "color": "red",
                    },
                ),
            ],
            style={"display": "flex", "justify-content": "flex-end"},
        ),
        *sliders,
        dcc.Input(id="search-input", type="text", placeholder="Введіть ISIN"),
        html.Button("▼", id="dropdown-button"),
        dcc.Dropdown(
            id="dropdown",
            options=[
                {"label": "Рекомендовані облігації", "value": "Рекомендовані облігації"}
            ]
            + [{"label": isin, "value": isin} for isin in raw_bonds["ISIN"]],
            placeholder="Виберіть ISIN",
            style={"display": "none"},
        ),
        html.Div(id="search-output"),
        html.H3(
            "Портфель облігацій", style={"text-align": "center", "margin-top": "20px"}
        ),
        html.Div(
            dash_table.DataTable(
                id="bag-table",
                columns=[{"name": col, "id": col} for col in formatted_bag.columns],
                data=formatted_bag.to_dict("records"),
                style_data_conditional=get_styleby_condition(formatted_bag),
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

    fig = plot_potential_payments(base_fig, potential_payments, monthly_bag)

    fig.update_layout(transition_duration=500)

    return fig


@callback(
    Output("search-output", "children"),
    [Input("search-input", "value"), Input("dropdown", "value")],
)
def update_search_output(input_value, selected_option):
    if selected_option == "Рекомендовані облігації":
        df = recommended_bonds
    elif input_value or selected_option:
        search_value = input_value or selected_option
        df = bonds.loc[bonds["ISIN"] == search_value]
    else:
        return None

    df = df.drop(
        columns=[
            "pay_date",
            "pay_val",
            "month_end",
            "emit_okpo",
            "cpcode_cfi",
            "sum_pay_val",
            "cptype",
        ]
    )
    df = df.drop_duplicates()
    df["issue_date"] = pd.to_datetime(df["issue_date"]).dt.strftime("%d-%m-%Y")
    df["maturity_date"] = df["maturity_date"].dt.strftime("%d-%m-%Y")
    df["profitability"] = df["profitability"].round(2)
    df = df.rename(columns=MAP_HEADINGS)

    table_data = df.to_dict("records")
    table_columns = [{"name": col, "id": col} for col in df.columns]

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
