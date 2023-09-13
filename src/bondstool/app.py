import base64

import numpy as np
import pandas as pd
import plotly.io as pio
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
from bondstool.data.bag import (
    format_bag,
    get_payment_schedule,
    merge_bonds_info,
    read_example_bag,
    verify_excel_file,
)
from bondstool.data.bonds import (
    add_exchange_rates,
    get_bonds_info,
    get_exchange_rates,
    get_recommended_bonds,
    normalize_payments,
)
from bondstool.layout import (
    BAG_TABLE_LAYOUT,
    DDC_STORE,
    DOWNLOAD_BUTTON_LAYOUT,
    RECOMMENDED_LABEL_LAYOUT,
    SCHEDULE_TABLE_LAYOUT,
    TITLE_LAYOUT,
    UPLOAD_BUTTON_LAYOUT,
)
from bondstool.utils import (
    MAP_HEADINGS,
    get_style_by_condition,
    get_xlsx,
    read_json,
)
from dash import ALL, Dash, Input, Output, State, callback, dash_table, dcc, html
from dash.exceptions import PreventUpdate

EXCHANGE_RATE = get_exchange_rates()

RAW_BONDS = get_bonds_info()
RAW_BONDS = add_exchange_rates(RAW_BONDS, EXCHANGE_RATE)

bonds = normalize_payments(RAW_BONDS)
BONDS = calculate_profitability(bonds)

DOC_URL, AUC_DATE = get_doc_url_date()

ISIN_DF = parse_xml_isins(get_auction_xml(DOC_URL))

TRADING_BONDS = filter_trading_bonds(ISIN_DF, bonds)


app = Dash(__name__)

SLIDER_STEPS = np.arange(0, 5000, 200)


def create_slider(id, index, recommended_bonds):
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
                id={"type": "isin_slider", "index": index},
            ),
        ]
    )


app.layout = html.Div(
    [
        html.Div(id="dummy-trigger", style={"display": "none"}),
        TITLE_LAYOUT,
        UPLOAD_BUTTON_LAYOUT,
        dcc.Graph(id="graph-with-slider"),
        html.Div(
            [
                html.H2(
                    f"Облігації доступні на аукціоні: {AUC_DATE}",
                    style={
                        "text-align": "center",
                        "margin": "1px 0",
                        "font-size": "25px",
                    },
                ),
            ],
            style={"display": "flex", "justify-content": "center"},
        ),
        RECOMMENDED_LABEL_LAYOUT,
        html.Div(id="sliders"),
        dcc.Input(id="search-input", type="text", placeholder="Введіть ISIN"),
        html.Button("▼", id="dropdown-button"),
        dcc.Dropdown(
            id="dropdown",
            options=[
                {
                    "label": "Рекомендовані облігації",
                    "value": "Рекомендовані облігації",
                }
            ]
            + [{"label": isin, "value": isin} for isin in RAW_BONDS["ISIN"]],
            placeholder="Виберіть ISIN",
            style={"display": "none"},
        ),
        html.Div(id="search-output"),
        BAG_TABLE_LAYOUT,
        SCHEDULE_TABLE_LAYOUT,
        DOWNLOAD_BUTTON_LAYOUT,
        DDC_STORE,
    ]
)


@callback(
    Output("intermediate-bag", "data"),
    Input("dummy-trigger", "n_clicks"),
)
def get_bag(n_clicks):
    bag = read_example_bag()
    bag = merge_bonds_info(bag, BONDS)
    return bag.to_json(date_format="iso", orient="split")


@callback(
    [
        Output("intermediate-payment-schedule", "data"),
        Output("intermediate-formatted-bag", "data"),
        Output("intermediate-monthly-bag", "data"),
    ],
    Input("intermediate-bag", "data"),
)
def get_bag_derivatives(data):

    dates_columns = ["pay_date", "month_end"]
    bag = read_json(data, dates_columns)

    if bag.empty:
        raise PreventUpdate

    payment_schedule = get_payment_schedule(bag)

    formatted_bag = format_bag(bag)

    monthly_bag = payments_by_month(bag)
    monthly_bag = fill_missing_months(monthly_bag)

    monthly_bag.reset_index(inplace=True)

    return (
        payment_schedule.to_json(date_format="iso", orient="split"),
        formatted_bag.to_json(date_format="iso", orient="split"),
        monthly_bag.to_json(date_format="iso", orient="split"),
    )


@callback(
    [
        Output("intermediate-recommended-bonds", "data"),
        Output("intermediate-base-fig", "data"),
    ],
    Input("intermediate-monthly-bag", "data"),
    prevent_initial_call=True,
)
def get_monthly_bag_derivatives(data):

    dates_columns = index_column = ["month_end"]
    monthly_bag = read_json(data, dates_columns, index_column)

    recommended_bonds = get_recommended_bonds(BONDS, monthly_bag)

    base_fig = make_base_monthly_payments_fig(monthly_bag)

    return (
        recommended_bonds.to_json(date_format="iso", orient="split"),
        base_fig.to_json(),
    )


@app.callback(
    [
        Output("intermediate-bag", "data", allow_duplicate=True),
        Output("warning-label1", "style"),
        Output("warning-label2", "style"),
        Output("bag-header", "children"),
        Output("schedule-header", "children"),
    ],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
    prevent_initial_call=True,
)
def update_data_and_objects(contents, filename):

    if contents is None:
        raise PreventUpdate

    _, data = contents.split(",")

    padding = "=" * (4 - (len(data) % 4))
    decoded_data = base64.b64decode(data + padding)

    bag = verify_excel_file(decoded_data)
    bag = pd.DataFrame(bag)
    map_headings = {
        "Кілть в портфелі": "quantity",
        "Загальна сума придбання": "expenditure",
        "Податок на прибуток ЮО (ПнПр)": "tax",
    }

    bag = bag.rename(columns=map_headings)
    bag = merge_bonds_info(bag, BONDS)

    bag_header = "Портфель облігацій"
    schedule_header = "Графік платежів"

    return (
        bag.to_json(date_format="iso", orient="split"),
        {"display": "none"},
        {"display": "none"},
        bag_header,
        schedule_header,
    )


@callback(
    Output("sliders", "children"),
    Input("intermediate-recommended-bonds", "data"),
    prevent_initial_call=True,
)
def get_sliders(data):

    dates_columns = ["maturity_date", "issue_date", "pay_date", "month_end"]
    recommended_bonds = read_json(data, dates_columns)

    sliders = [
        create_slider(isin, index, recommended_bonds)
        for index, isin in enumerate(ISIN_DF["ISIN"])
    ]

    return sliders


@callback(
    Output("graph-with-slider", "figure"),
    [
        Input("intermediate-base-fig", "data"),
        Input("intermediate-monthly-bag", "data"),
        Input({"type": "isin_slider", "index": ALL}, "value"),
    ],
    prevent_initial_call=True,
)
def update_figure(base_fig_data, monthly_bag_data, amounts):

    dates_columns = index_column = ["month_end"]

    base_fig = pio.from_json(base_fig_data)
    monthly_bag = read_json(monthly_bag_data, dates_columns, index_column)

    potential_payments = calc_potential_payments(
        TRADING_BONDS, amounts, monthly_bag, ISIN_DF
    )

    fig = plot_potential_payments(base_fig, potential_payments, monthly_bag)

    fig.update_layout(transition_duration=500)

    return fig


@callback(
    Output("search-output", "children"),
    [
        Input("search-input", "value"),
        Input("dropdown", "value"),
        Input("intermediate-recommended-bonds", "data"),
    ],
)
def update_search_output(input_value, selected_option, data):

    if input_value is not None or selected_option is not None:

        if data is None:
            raise PreventUpdate

        if selected_option == "Рекомендовані облігації":

            dates_columns = ["maturity_date", "issue_date", "pay_date", "month_end"]

            df = read_json(data, dates_columns)

        elif input_value or selected_option:
            search_value = input_value or selected_option
            df = BONDS.loc[BONDS["ISIN"] == search_value]
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
                "exchange_rate",
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


@callback(
    [
        Output("bag-table", "columns"),
        Output("bag-table", "data"),
        Output("bag-table", "style_data_conditional"),
    ],
    [Input("intermediate-formatted-bag", "data")],
    prevent_initial_call=True,
)
def get_bag_table(data):

    dates_columns = ["Дата погашеня"]
    formatted_bag = read_json(data, dates_columns)

    columns = [{"name": col, "id": col} for col in formatted_bag.columns]
    table_data = formatted_bag.to_dict("records")
    style_data_conditional = get_style_by_condition(formatted_bag)

    return columns, table_data, style_data_conditional


@callback(
    [Output("payment-schedule", "columns"), Output("payment-schedule", "data")],
    [Input("intermediate-payment-schedule", "data")],
    prevent_initial_call=True,
)
def get_schedule_table(data):

    dates_columns = ["Дата"]
    payment_schedule = read_json(data, dates_columns)

    columns = [{"name": col, "id": col} for col in payment_schedule.columns]
    table_data = payment_schedule.to_dict("records")

    return columns, table_data


@callback(
    Output("download-dataframe-xlsx", "data"),
    [
        Input("btn_xlsx", "n_clicks"),
        Input("intermediate-formatted-bag", "data"),
        Input("intermediate-payment-schedule", "data"),
    ],
    prevent_initial_call=True,
)
def download_xlsx(n_clicks, formatted_bag_data, payment_schedule_data):
    if n_clicks is None:
        return None

    if formatted_bag_data is None or payment_schedule_data is None:
        raise PreventUpdate

    dates_columns = ["Дата погашеня", "Дата"]

    formatted_bag = read_json(formatted_bag_data, dates_columns)
    payment_schedule = read_json(payment_schedule_data, dates_columns)

    xlsx_bytes = get_xlsx(formatted_bag, payment_schedule)

    return dcc.send_bytes(xlsx_bytes, "OVDP_analysis.xlsx")


if __name__ == "__main__":
    app.run(debug=True)
