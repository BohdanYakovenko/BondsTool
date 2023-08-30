import io
from datetime import datetime

import pandas as pd

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

    bytes_io = io.BytesIO()
    xslx_writer = pd.ExcelWriter(bytes_io, engine="xlsxwriter")

    bag.to_excel(xslx_writer, sheet_name="Bag", index=False)
    schedule.to_excel(xslx_writer, sheet_name="Schedule", index=False)

    worksheet_bag = xslx_writer.sheets["Bag"]
    worksheet_schedule = xslx_writer.sheets["Schedule"]

    max_lengths_bag = [
        max(bag[col].astype(str).apply(len).max(), len(col)) for col in bag.columns
    ]
    max_lengths_schedule = [
        max(schedule[col].astype(str).apply(len).max(), len(col))
        for col in schedule.columns
    ]

    for i, max_length in enumerate(max_lengths_bag):
        worksheet_bag.set_column(i, i, max_length + 2)

    for i, max_length in enumerate(max_lengths_schedule):
        worksheet_schedule.set_column(i, i, max_length + 2)

    xslx_writer.close()
    bytes_io.seek(0)

    return bytes_io.getvalue()
