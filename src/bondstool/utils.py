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
    "expected return": "Сума погашення",
    "profit before tax": "Прибуток без податку",
    "profit after tax": "Прибуток після податку",
    "profit per bond": "Прибуток на облігацію",
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
