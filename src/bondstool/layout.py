import numpy as np
from bondstool.utils import IMAGE_PATH, get_image_element
from dash import dash_table, dcc, html

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


TITLE_LAYOUT = html.Div(
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
)


UPLOAD_BUTTON_LAYOUT = html.Div(
    [
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Перетягніть або ", html.A("Виберіть файл")]),
            style={
                "width": "95%",
                "height": "40px",
                "lineHeight": "40px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px auto",
                "cursor": "pointer",
            },
        ),
        html.H3(
            "Дані відображенні нижче згенеровані автоматично для ПРИКЛАДУ",
            style={
                "text-align": "center",
                "margin-top": "20px",
                "font-size": "20px",
                "color": "red",
            },
            id="warning-label1",
        ),
        html.H4(
            "Завантажте свій файл для аналізу даних",
            style={
                "text-align": "center",
                "margin-top": "20px",
                "font-size": "20px",
                "color": "red",
            },
            id="warning-label2",
        ),
    ]
)


AUCTION_DATE_LABEL_LAYOUT = html.Div(
    [
        html.H2(
            children=[],
            style={
                "text-align": "center",
                "margin": "1px 0",
                "font-size": "25px",
            },
            id="auction-label",
        ),
    ],
    style={"display": "flex", "justify-content": "center"},
)


RECOMMENDED_LABEL_LAYOUT = html.Div(
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
)


DROPDOWN_LIST_LAYOUT = dcc.Dropdown(
    id="dropdown",
    options=[],
    placeholder="Виберіть ISIN",
    style={"display": "none"},
)


BAG_TABLE_LAYOUT = html.Div(
    [
        html.H3(
            children="Портфель облігацій - ДЛЯ ПРИКЛАДУ",
            style={
                "text-align": "center",
                "margin-top": "20px",
                "font-size": "20px",
            },
            id="bag-header",
        ),
        dash_table.DataTable(id="bag-table"),
    ]
)

SCHEDULE_TABLE_LAYOUT = html.Div(
    [
        html.H4(
            children="Графік платежів - ДЛЯ ПРИКЛАДУ",
            style={
                "text-align": "center",
                "margin-top": "20px",
                "font-size": "20px",
            },
            id="schedule-header",
        ),
        html.Div(
            dash_table.DataTable(
                id="payment-schedule",
            ),
            style={"margin-top": "10px", "margin-bottom": "20px"},
        ),
    ]
)

DOWNLOAD_BUTTON_LAYOUT = html.Div(
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
)

DDC_STORE = html.Div(
    [
        dcc.Download(id="download-dataframe-xlsx"),
        dcc.Store(id="intermediate-bag"),
        dcc.Store(id="intermediate-raw-bonds"),
        dcc.Store(id="intermediate-bonds"),
        dcc.Store(id="intermediate-auc-date"),
        dcc.Store(id="intermediate-isin-df"),
        dcc.Store(id="intermediate-trading-bonds"),
        dcc.Store(id="intermediate-payment-schedule"),
        dcc.Store(id="intermediate-formatted-bag"),
        dcc.Store(id="intermediate-monthly-bag"),
        dcc.Store(id="intermediate-recommended-bonds"),
        dcc.Store(id="intermediate-base-fig"),
    ]
)
