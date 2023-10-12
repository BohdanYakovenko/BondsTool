import base64

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
    AUCTION_DATE_LABEL_LAYOUT,
    BAG_TABLE_LAYOUT,
    DDC_STORE,
    DOWNLOAD_BUTTON_LAYOUT,
    DROPDOWN_LIST_LAYOUT,
    RECOMMENDED_LABEL_LAYOUT,
    SCHEDULE_TABLE_LAYOUT,
    TITLE_LAYOUT,
    UPLOAD_BUTTON_LAYOUT,
    create_slider,
)
from bondstool.utils import (
    JSON_STORE_KWARGS,
    MAP_HEADINGS,
    get_style_by_condition,
    get_xlsx,
    read_json,
)
from dash import ALL, Dash, Input, Output, State, callback, dash_table, dcc, html
from dash.exceptions import PreventUpdate

app = Dash(__name__)


app.layout = html.Div(
    [
        html.Div(id="dummy-trigger", style={"display": "none"}),
        TITLE_LAYOUT,
        UPLOAD_BUTTON_LAYOUT,
        dcc.Graph(id="graph-with-slider"),
        AUCTION_DATE_LABEL_LAYOUT,
        RECOMMENDED_LABEL_LAYOUT,
        html.Div(id="sliders"),
        dcc.Input(id="search-input", type="text", placeholder="Введіть ISIN"),
        html.Button("▼", id="dropdown-button"),
        DROPDOWN_LIST_LAYOUT,
        html.Div(id="search-output"),
        BAG_TABLE_LAYOUT,
        SCHEDULE_TABLE_LAYOUT,
        DOWNLOAD_BUTTON_LAYOUT,
        DDC_STORE,
    ]
)


@callback(
    [
        Output("intermediate-bag", "data"),
        Output("intermediate-raw-bonds", "data"),
        Output("intermediate-bonds", "data"),
        Output("intermediate-auc-date", "data"),
        Output("intermediate-isin-df", "data"),
        Output("intermediate-trading-bonds", "data"),
    ],
    Input("dummy-trigger", "n_clicks"),
)
def get_bag(n_clicks):

    exchange_rates = get_exchange_rates()

    raw_bonds = get_bonds_info()
    raw_bonds = add_exchange_rates(raw_bonds, exchange_rates)

    bonds = normalize_payments(raw_bonds)
    bonds = calculate_profitability(bonds)

    doc_url, auc_date = get_doc_url_date()
    auc_date = str(auc_date)

    isin_df = parse_xml_isins(get_auction_xml(doc_url))

    trading_bonds = filter_trading_bonds(isin_df, bonds)

    bag = read_example_bag()
    bag = merge_bonds_info(bag, bonds)

    return (
        bag.to_json(**JSON_STORE_KWARGS),
        raw_bonds.to_json(**JSON_STORE_KWARGS),
        bonds.to_json(**JSON_STORE_KWARGS),
        auc_date,
        isin_df.to_json(**JSON_STORE_KWARGS),
        trading_bonds.to_json(**JSON_STORE_KWARGS),
    )


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
        payment_schedule.to_json(**JSON_STORE_KWARGS),
        formatted_bag.to_json(**JSON_STORE_KWARGS),
        monthly_bag.to_json(**JSON_STORE_KWARGS),
    )


@callback(
    [
        Output("intermediate-recommended-bonds", "data"),
        Output("intermediate-base-fig", "data"),
    ],
    [Input("intermediate-monthly-bag", "data"), Input("intermediate-bonds", "data")],
    prevent_initial_call=True,
)
def get_monthly_bag_derivatives(monthly_bag_data, bonds_data):

    dates_columns = ["month_end", "maturity_date", "pay_date"]
    index_column = ["month_end"]

    monthly_bag = read_json(monthly_bag_data, dates_columns, index_column)
    bonds = read_json(bonds_data, dates_columns)

    recommended_bonds = get_recommended_bonds(bonds, monthly_bag)

    base_fig = make_base_monthly_payments_fig(monthly_bag)

    return (
        recommended_bonds.to_json(**JSON_STORE_KWARGS),
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
    [Input("upload-data", "contents"), Input("intermediate-bonds", "data")],
    [State("upload-data", "filename")],
    prevent_initial_call=True,
)
def update_data_and_objects(contents, bonds_data, filename):

    if contents is None:
        raise PreventUpdate

    dates_columns = [
        "month_end",
        "maturity_date",
        "pay_date",
    ]
    bonds = read_json(bonds_data, dates_columns)

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
    bag = merge_bonds_info(bag, bonds)

    bag_header = "Портфель облігацій"
    schedule_header = "Графік платежів"

    return (
        bag.to_json(**JSON_STORE_KWARGS),
        {"display": "none"},
        {"display": "none"},
        bag_header,
        schedule_header,
    )


@callback(Output("auction-label", "children"), Input("intermediate-auc-date", "data"))
def get_auction_header(auc_date):

    children = f"Облігації доступні на аукціоні: {auc_date}"

    return children


@callback(Output("dropdown", "options"), Input("intermediate-raw-bonds", "data"))
def get_dropdown_options(data):

    dates_columns = ["maturity_date", "issue_date"]
    raw_bonds = read_json(data, dates_columns)

    options = [
        {
            "label": "Рекомендовані облігації",
            "value": "Рекомендовані облігації",
        }
    ] + [{"label": isin, "value": isin} for isin in raw_bonds["ISIN"]]

    return options


@callback(
    Output("sliders", "children"),
    [
        Input("intermediate-recommended-bonds", "data"),
        Input("intermediate-isin-df", "data"),
    ],
    prevent_initial_call=True,
)
def get_sliders(recommended_data, isin_df_data):

    dates_columns = ["maturity_date", "issue_date", "pay_date", "month_end"]
    recommended_bonds = read_json(recommended_data, dates_columns)
    isin_df = read_json(isin_df_data)

    sliders = [
        create_slider(isin, index, recommended_bonds)
        for index, isin in enumerate(isin_df["ISIN"])
    ]

    return sliders


@callback(
    Output("graph-with-slider", "figure"),
    [
        Input("intermediate-base-fig", "data"),
        Input("intermediate-monthly-bag", "data"),
        Input("intermediate-trading-bonds", "data"),
        Input("intermediate-isin-df", "data"),
        Input({"type": "isin_slider", "index": ALL}, "value"),
    ],
    prevent_initial_call=True,
)
def update_figure(
    base_fig_data, monthly_bag_data, trading_bonds_data, isin_df_data, amounts
):

    if not amounts:
        raise PreventUpdate

    dates_columns = ["month_end", "maturity_date", "pay_date"]
    index_column = ["month_end"]

    base_fig = pio.from_json(base_fig_data)
    monthly_bag = read_json(monthly_bag_data, dates_columns, index_column)
    trading_bonds = read_json(trading_bonds_data, dates_columns)
    isin_df = read_json(isin_df_data)

    potential_payments = calc_potential_payments(
        trading_bonds, amounts, monthly_bag, isin_df
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
        Input("intermediate-bonds", "data"),
    ],
)
def update_search_output(input_value, selected_option, recommended_data, bonds_data):

    if input_value is not None or selected_option is not None:

        if recommended_data is None:
            raise PreventUpdate

        dates_columns = [
            "maturity_date",
            "issue_date",
            "pay_date",
            "month_end",
        ]

        if selected_option == "Рекомендовані облігації":

            df = read_json(recommended_data, dates_columns)

        elif input_value or selected_option:
            search_value = input_value or selected_option

            bonds = read_json(bonds_data, dates_columns)
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

    cols_to_round = [
        "Загальна сума придбання",
        "Податок (ПнПр)",
        "Курс валют",
        "Сума погашення, UAH",
        "Прибуток без податку",
        "Прибуток після податку",
        "Прибуток на облігацію",
        "Прибутковість, %",
    ]

    columns = []
    for col in formatted_bag.columns:
        cfg = {"name": col, "id": col}
        if col in cols_to_round:
            cfg["type"] = "numeric"
            cfg["format"] = {"specifier": ".2f"}

        columns.append(cfg)

    table_data = formatted_bag.to_dict("records")
    style_data_conditional = get_style_by_condition(formatted_bag)

    return columns, table_data, style_data_conditional


@callback(
    [Output("payment-schedule", "columns"), Output("payment-schedule", "data")],
    [Input("intermediate-payment-schedule", "data")],
    prevent_initial_call=True,
)
def get_schedule_table(data):

    payment_schedule = read_json(data)

    cols_to_round = [
        "Сума, UAH",
    ]

    columns = []
    for col in payment_schedule.columns:
        cfg = {"name": col, "id": col}
        if col in cols_to_round:
            cfg["type"] = "numeric"
            cfg["format"] = {"specifier": ".2f"}

        columns.append(cfg)

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

    dates_columns = ["Дата погашеня"]

    formatted_bag = read_json(formatted_bag_data, dates_columns)
    payment_schedule = read_json(payment_schedule_data, dates_columns)

    xlsx_bytes = get_xlsx(formatted_bag, payment_schedule)

    return dcc.send_bytes(xlsx_bytes, "OVDP_analysis.xlsx")


if __name__ == "__main__":
    app.run(debug=True)
