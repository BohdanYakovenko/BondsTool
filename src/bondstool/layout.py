from bondstool.utils import IMAGE_PATH, get_image_element
from dash import dash_table, dcc, html

TITLE = html.Div(
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


UPLOAD = dcc.Upload(
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
)

RECOMMENDED_LABEL = html.Div(
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

BAG_TABLE = html.Div(
    [
        html.H3(
            "Портфель облігацій",
            style={
                "text-align": "center",
                "margin-top": "20px",
                "font-size": "20px",
            },
        ),
        dash_table.DataTable(id="bag-table"),
    ]
)

SCHEDULE_TABLE = html.Div(
    [
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
            ),
            style={"margin-top": "10px", "margin-bottom": "20px"},
        ),
    ]
)

DOWNLOAD = html.Div(
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
        dcc.Store(id="intermediate-payment-schedule"),
        dcc.Store(id="intermediate-formatted-bag"),
        dcc.Store(id="intermediate-monthly-bag"),
        dcc.Store(id="intermediate-recommended-bonds"),
        dcc.Store(id="intermediate-base-fig"),
    ]
)
