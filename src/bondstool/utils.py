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
