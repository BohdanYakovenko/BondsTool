import base64
import io

import dash
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
from bondstool.data.bag import (
    format_bag,
    get_payment_schedule,
    merge_bonds_info,
    read_bag_info,
)
from bondstool.data.bonds import (
    add_exchange_rates,
    get_bonds_info,
    get_exchange_rates,
    get_recommended_bonds,
    normalize_payments,
)
from bondstool.utils import (
    IMAGE_PATH,
    MAP_HEADINGS,
    get_image_element,
    get_style_by_condition,
    get_xlsx,
)
from dash import Dash, Input, Output, State, callback, dash_table, dcc, html
from dash.exceptions import PreventUpdate

exchange_rates = get_exchange_rates()

raw_bonds = get_bonds_info()
raw_bonds = add_exchange_rates(raw_bonds, exchange_rates)

bonds = normalize_payments(raw_bonds)
bonds = calculate_profitability(bonds)

bag = read_bag_info()
bag = merge_bonds_info(bag, bonds)

doc_url, auc_date = get_doc_url_date()

isin_df = parse_xml_isins(get_auction_xml(doc_url))

trading_bonds = filter_trading_bonds(isin_df, bonds)

payment_schedule = get_payment_schedule(bag)
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


def generate_layout(formatted_bag, payment_schedule, sliders):

    layout = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        get_image_element(IMAGE_PATH),
                        style={
                            "flex": "0",
                            "float": "left",
                        },
                    ),
                    html.Div(
                        html.H1(
                            "Аналітика облігацій",
                            style={
                                "text-align": "center",
                                "font-size": "30px",
                                "width": "100%",
                                "flex": "1",
                            },
                        ),
                    ),
                ],
                style={
                    "display": "flex",
                    "justify-content": "center",
                    "align-items": "center",
                },
            ),
            dcc.Upload(
                id="upload-data",
                children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
                style={
                    "width": "100%",
                    "height": "60px",
                    "lineHeight": "60px",
                    "borderWidth": "1px",
                    "borderStyle": "dashed",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "10px",
                },
            ),
            html.Div(id="output-data-upload"),
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
                    {
                        "label": "Рекомендовані облігації",
                        "value": "Рекомендовані облігації",
                    }
                ]
                + [{"label": isin, "value": isin} for isin in raw_bonds["ISIN"]],
                placeholder="Виберіть ISIN",
                style={"display": "none"},
            ),
            html.Div(id="search-output"),
            html.H3(
                "Портфель облігацій",
                style={
                    "text-align": "center",
                    "margin-top": "20px",
                    "font-size": "20px",
                },
            ),
            html.Div(
                dash_table.DataTable(
                    id="bag-table",
                    columns=[{"name": col, "id": col} for col in formatted_bag.columns],
                    data=formatted_bag.to_dict("records"),
                    style_data_conditional=get_style_by_condition(formatted_bag),
                ),
                style={"margin-top": "10px"},
            ),
            html.H4(
                "Графік платежів",
                style={
                    "text-align": "center",
                    "margin-top": "20px",
                    "font-size": "20px",
                },
            ),
            html.Div(
                dash_table.DataTable(
                    id="payment-schedule",
                    columns=[
                        {"name": col, "id": col} for col in payment_schedule.columns
                    ],
                    data=payment_schedule.to_dict("records"),
                ),
                style={"margin-top": "10px", "margin-bottom": "20px"},
            ),
            html.Div(
                html.Button(
                    "Завантажити ексель",
                    id="btn_xlsx",
                    style={
                        "font-weight": "bold",
                        "padding": "10px 20px",
                        "border": "none",
                        "border-radius": "5px",
                        "cursor": "pointer",
                    },
                ),
                style={
                    "display": "flex",
                    "justify-content": "flex-end",
                    "margin-right": "20px",
                },
            ),
            dcc.Download(id="download-dataframe-xlsx"),
        ]
    )

    return layout


app.layout = generate_layout(formatted_bag, payment_schedule, sliders)


def parse_contents(contents, filename):
    global bag, payment_schedule, formatted_bag, monthly_bag, recommended_bonds, base_fig, sliders

    # content_type, content_string = contents.split(',')

    # decoded = base64.b64decode(content_string)
    # try:
    #    if 'xlsx' in filename:
    #        # Assume that the user uploaded an excel file
    #        df = pd.read_excel(io.BytesIO(decoded))
    # except Exception as e:
    #    print(e)
    #    return html.Div([
    #        'There was an error processing this file.'
    #    ])

    bag = contents
    map_headings = {
        "Кілть в портфелі": "quantity",
        "Загальна сума придбання": "expenditure",
        "Податок на прибуток ЮО (ПнПр)": "tax",
    }

    bag = bag.rename(columns=map_headings)
    bag = merge_bonds_info(bag, bonds)

    payment_schedule = get_payment_schedule(bag)
    formatted_bag = format_bag(bag)

    monthly_bag = payments_by_month(bag)
    monthly_bag = fill_missing_months(monthly_bag)

    recommended_bonds = get_recommended_bonds(bonds, monthly_bag)

    base_fig = make_base_monthly_payments_fig(monthly_bag)

    sliders = [create_slider(isin) for isin in isin_df["ISIN"].values]

    layout = generate_layout(formatted_bag, payment_schedule, sliders)

    return layout


sliders_input = [Input(isin, "value") for isin in isin_df["ISIN"].values]

uploaded_data = None


@app.callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    State("upload-data", "last_modified"),
)
def update_data_and_objects(contents, refresh_clicks, filename):
    global uploaded_data, bag, payment_schedule, formatted_bag, monthly_bag, recommended_bonds, base_fig

    if dash.callback_context.triggered:
        triggered_id = dash.callback_context.triggered[0]["prop_id"].split(".")[0]

        if triggered_id == "upload-data":
            if uploaded_data is not None:
                raise PreventUpdate

            # Process the uploaded file, assuming it's an Excel file
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)
            df = pd.read_excel(io.BytesIO(decoded))

            # Store the uploaded data in the global variable
            uploaded_data = df

            app.layout = html.Div()

            app.layout = parse_contents(uploaded_data, filename)

            return app.layout

        elif triggered_id == "refresh-button":
            if uploaded_data is None:
                raise PreventUpdate

            # Process the uploaded data and update the objects

        # Generate the updated layout

        return app.layout

    raise PreventUpdate


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
    Output("download-dataframe-xlsx", "data"),
    Input("btn_xlsx", "n_clicks"),
    prevent_initial_call=True,
)
def download_xlsx(n_clicks):

    xlsx_bytes = get_xlsx(formatted_bag, payment_schedule)

    return dcc.send_bytes(xlsx_bytes, "OVDP_analysis.xlsx")


if __name__ == "__main__":
    app.run(debug=True)
