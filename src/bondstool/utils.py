from datetime import datetime

import pandas as pd


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


def get_style_by_condition(df: pd.DataFrame, column="pay_date"):
    style_conditional = []
    for index, row in df.iterrows():
        if pd.isna(row[column]):
            style_conditional.append(
                {
                    "if": {"row_index": index},
                    "backgroundColor": "rgb(237, 237, 237)",
                }
            )
    return style_conditional
