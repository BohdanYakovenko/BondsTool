import base64
import io
import os
from datetime import datetime
from io import StringIO

import pandas as pd
from dash import html

IMAGE_PATH = "assets/logo.png"

JSON_STORE_KWARGS = {
    "date_format": "iso",
    "orient": "split"
}

MAP_HEADINGS = {
    "nominal": "Номінал",
    "auk_proc": "Процентна ставка",
    "maturity_date": "Дата погашення",
    "issue_date": "Дата випуску",
    "type": "Вид",
    "pay_period": "Купонний період",
    "currency": "Валюта",
    "emit_name": "Назва емітента",
    "cptype_nkcpfr": "Вид НКЦПФР",
    "total_bonds": "Кількість облігацій",
    "profitability": "Прибутковість, %",
    "quantity": "Кількість",
    "expenditure": "Загальна сума придбання",
    "tax": "Податок (ПнПр)",
    "pay_date": "Дата погашеня",
    "expected return": "Сума погашення, UAH",
    "profit before tax": "Прибуток без податку",
    "profit after tax": "Прибуток після податку",
    "profit per bond": "Прибуток на облігацію",
    "exchange_rate": "Курс валют",
}


def search_by_isin(isin: str, df: pd.DataFrame):
    return df.loc[df["ISIN"] == isin]


def round_to_month_end(series: pd.Series):
    return series + pd.tseries.offsets.MonthEnd(0)


def truncate_past_dates(df: pd.DataFrame, date=None, date_col="pay_date"):
    if not date:
        date = datetime.today()

    return df.loc[df[date_col] >= date]


def split_dataframe(df: pd.DataFrame, column="pay_date"):

    condition = pd.isna(df[column])
    df_satisfying = df[condition]
    df_not_satisfying = df[~condition]

    return df_not_satisfying, df_satisfying


def get_style_by_condition(
    df: pd.DataFrame, column="Дата погашеня", condition="Погашена"
):
    style_conditional = []
    for index, row in df.iterrows():
        if row[column] == condition:
            style_conditional.append(
                {
                    "if": {"row_index": index},
                    "backgroundColor": "rgb(237, 237, 237)",
                }
            )
    return style_conditional


def get_xlsx(bag: pd.DataFrame, schedule: pd.DataFrame):

    with io.BytesIO() as bytes_io:

        with pd.ExcelWriter(bytes_io, engine="xlsxwriter") as xslx_writer:

            bag.to_excel(xslx_writer, sheet_name="Bag", index=False)
            schedule.to_excel(xslx_writer, sheet_name="Schedule", index=False)

            for sheet in xslx_writer.sheets.values():
                sheet.autofit()

        bytes_io.seek(0)

        return bytes_io.getvalue()


def encode_image(image_path):

    if os.path.exists(image_path):

        with open(image_path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        return image_base64

    return None


def get_image_element(image_path):

    encoded_image = encode_image(image_path)

    if encoded_image:
        return html.Img(
            src="data:image/png;base64,{}".format(encoded_image),
            style={
                "width": "auto",
                "height": "80px",
                "align-self": "center",
                "margin-right": "20px",
            },
        )

    else:
        return None


def read_json(data, date_columns=None, index_col=None, orient="split"):
    if isinstance(data, str):
        data = StringIO(data)

    convert_dates = True if date_columns is None else date_columns
    df = pd.read_json(data, orient=orient, convert_dates=convert_dates)

    if index_col is not None:
        df.set_index(index_col, inplace=True)

    return df
