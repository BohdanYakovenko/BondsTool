import base64
import io
import json
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

#bag = read_bag_info()
#bag = merge_bonds_info(bag, bonds)

doc_url, auc_date = get_doc_url_date()

isin_df = parse_xml_isins(get_auction_xml(doc_url))

trading_bonds = filter_trading_bonds(isin_df, bonds)

#payment_schedule = get_payment_schedule(bag)
#formatted_bag = format_bag(bag)

#monthly_bag = payments_by_month(bag)
#monthly_bag = fill_missing_months(monthly_bag)

#recommended_bonds = get_recommended_bonds(bonds, monthly_bag)

#base_fig = make_base_monthly_payments_fig(monthly_bag)


app = Dash(__name__)

SLIDER_STEPS = np.arange(0, 5000, 200)


def create_slider(id, recommended_bonds):
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


#sliders = [create_slider(isin) for isin in isin_df["ISIN"].values]


app.layout = html.Div(
        [
            html.Div(id='dummy-trigger', style={'display': 'none'}),
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
            html.Div(id="bag-table"),
            html.H4(
                "Графік платежів",
                style={
                    "text-align": "center",
                    "margin-top": "20px",
                    "font-size": "20px",
                },
            ),
            html.Div(id="payment-schedule"),
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

            dcc.Store(id='intermediate-bag'),
            dcc.Store(id="intermediate-payment-schedule"),
            dcc.Store(id="intermediate-formatted-bag"),
            dcc.Store(id="intermediate-monthly-bag"),
            dcc.Store(id="intermediate-recommended-bonds"),
            dcc.Store(id="intermediate-base-fig")
        ]
    )


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

    _, data = contents.split(',')

    padding = '=' * (4 - (len(data) % 4))
    decoded_data = base64.b64decode(data + padding)

    bag = pd.read_excel(io.BytesIO(decoded_data))
    bag = pd.DataFrame(bag)
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

    return formatted_bag, payment_schedule, recommended_bonds, base_fig, sliders


sliders_input = [Input(isin, "value") for isin in isin_df["ISIN"].values]

uploaded_data = None


@callback(Output('intermediate-bag', 'data', allow_duplicate=True), 
        Input('dummy-trigger', 'children'),
        prevent_initial_call=True)
def get_bag(_):

    bag = read_bag_info()
    bag = merge_bonds_info(bag, bonds)

    return bag.to_json(date_format='iso', orient='split')


@callback(
    [Output("intermediate-payment-schedule", 'data'),
     Output("intermediate-formatted-bag", 'data'),
     Output("intermediate-monthly-bag", 'data')],
    Input("intermediate-bag", 'data')
    )
def get_bag_derivatives(data):

    bag = json.loads(data)

    payment_schedule = get_payment_schedule(bag)

    formatted_bag = format_bag(bag)

    monthly_bag = payments_by_month(bag)
    monthly_bag = fill_missing_months(monthly_bag)

    return (payment_schedule.to_json(date_format='iso', orient='split'),
            formatted_bag.to_json(date_format='iso', orient='split'),
            monthly_bag.to_json(date_format='iso', orient='split'))


@callback(
    [Output("intermediate-recommended-bonds", 'data'),
     Output("intermediate-base-fig", 'data')],
    Input('intermediate-monthly-bag', 'data')
    )
def get_monthly_bag_derivatives(data):

    monthly_bag = json.loads(data)

    recommended_bonds = get_recommended_bonds(bonds, monthly_bag)

    base_fig = make_base_monthly_payments_fig(monthly_bag)

    return (recommended_bonds.to_json(date_format='iso', orient='split'),
            base_fig.to_json(date_format='iso', orient='split'))



@app.callback(
    [Output("output-data-upload", "children"),
     Output('intermediate-bag', "data", allow_duplicate=True)],
    [Input("upload-data", "contents")],
    [State("upload-data", "filename")],
    prevent_initial_call=True
)
def update_data_and_objects(contents, filename):

    if contents is None:
        raise PreventUpdate

    _, data = contents.split(',')

    padding = '=' * (4 - (len(data) % 4))
    decoded_data = base64.b64decode(data + padding)

    bag = pd.read_excel(io.BytesIO(decoded_data))
    bag = pd.DataFrame(bag)
    map_headings = {
        "Кілть в портфелі": "quantity",
        "Загальна сума придбання": "expenditure",
        "Податок на прибуток ЮО (ПнПр)": "tax",
    }

    bag = bag.rename(columns=map_headings)
    bag = merge_bonds_info(bag, bonds)

    return bag.to_json(date_format='iso', orient='split')


@callback(
    Output("sliders", 'data'),
    Input('intermediate-recommended-bonds', 'data')
    )
def get_sliders(data):

    if data is None:
        raise PreventUpdate

    recommended_bonds = json.loads(data)

    sliders = [create_slider(isin, recommended_bonds) for isin in isin_df["ISIN"].values]

    return sliders

    
@callback(
    [Output("graph-with-slider", "figure"), *sliders_input],
    [Input("intermediate-base-fig", "data"),
    Input("intermediate-monthly-bag", "data")],
    )
def update_figure(base_fig_data, monthly_bag_data, *amounts):

    base_fig = json.loads(base_fig_data)
    monthly_bag = json.loads(monthly_bag_data)

    potential_payments = calc_potential_payments(
        trading_bonds, amounts, monthly_bag, isin_df
    )

    fig = plot_potential_payments(base_fig, potential_payments, monthly_bag)

    fig.update_layout(transition_duration=500)

    return fig


@callback(
    Output("search-output", "children"),
    [Input("search-input", "value"),
     Input("dropdown", "value"),
     Input("intermediate-recommended-bonds", "data")],
)
def update_search_output(input_value, selected_option, data):

 if input_value is not None and selected_option is not None:
        recommended_bonds = json.load(data)

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


@callback(Output("bag-table", "table"),
        [Input("intermediate-formatted-bag", "data")]
        )
def get_bag_table(data):

    formatted_bag = json.load(data)

    table = html.Div(
            dash_table.DataTable(
                    id="bag-table",
                    columns=[{"name": col, "id": col} for col in formatted_bag.columns],
                    data=formatted_bag.to_dict("records"),
                    style_data_conditional=get_style_by_condition(formatted_bag),
                ),
                style={"margin-top": "10px"})
    
    return table


@callback(Output("payment-schedule", "table"),
        [Input("intermediate-payment-schedule", "data")]
        )
def get_schedule_table(data):

    payment_schedule = json.load(data)

    table = html.Div(
                dash_table.DataTable(
                    id="payment-schedule",
                    columns=[
                        {"name": col, "id": col} for col in payment_schedule.columns
                    ],
                    data=payment_schedule.to_dict("records"),
                ),
                style={"margin-top": "10px", "margin-bottom": "20px"},
            ),
    
    return table


@callback(
    Output("download-dataframe-xlsx", "data"),
    [Input("btn_xlsx", "n_clicks"),
     Input("intermediate-formatted-bag", 'data'),
     Input("intermediate-payment-schedule", 'data')],
    prevent_initial_call=True,
)
def download_xlsx(n_clicks, formatted_bag_data, payment_schedule_data):

    formatted_bag = json.load(formatted_bag_data)
    payment_schedule = json.load(payment_schedule_data)

    xlsx_bytes = get_xlsx(formatted_bag, payment_schedule)

    return dcc.send_bytes(xlsx_bytes, "OVDP_analysis.xlsx")


if __name__ == "__main__":
    app.run(debug=True)
