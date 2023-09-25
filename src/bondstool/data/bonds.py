import io
from io import StringIO

import pandas as pd
import requests
from bondstool.utils import round_to_month_end, truncate_past_dates

BONDS_URL = "https://bank.gov.ua/depo_securities?json"
CURRENCY_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json"


def get_bonds_info():
    json_data = requests.get(url=BONDS_URL).text

    json_io = StringIO(json_data)

    bonds = pd.read_json(json_io, orient="records")

    bonds = bonds[bonds["cptype"] != "OZDP"]

    map_headings = {
        "cpcode": "ISIN",
        "pgs_date": "maturity_date",
        "razm_date": "issue_date",
        "cpdescr": "type",
        "val_code": "currency",
    }

    bonds = bonds.rename(columns=map_headings)
    bonds["maturity_date"] = pd.to_datetime(bonds["maturity_date"])

    return bonds


def get_exchange_rates():
    json_data = requests.get(url=CURRENCY_URL).text

    json_stream = io.StringIO(json_data)

    currencies = pd.read_json(json_stream)

    usd_and_eur = currencies[currencies["r030"].isin([840, 978])]

    uah = {"rate": 1, "cc": "UAH"}

    uah_df = pd.DataFrame([uah])

    exchange_rates = pd.concat([usd_and_eur, uah_df], ignore_index=True)

    return exchange_rates


def add_exchange_rates(bonds: pd.DataFrame, exchange_rates: pd.DataFrame):

    bonds = bonds.merge(
        exchange_rates[["cc", "rate"]], left_on="currency", right_on="cc", how="left"
    )
    bonds.rename(columns={"rate": "exchange_rate"}, inplace=True)

    bonds.drop(columns=["cc"], inplace=True)

    return bonds


def unpack_payments(payments_col):
    df = pd.DataFrame(payments_col)
    df = df.groupby("pay_date")[["pay_val"]].sum().reset_index()

    return df.to_dict(orient="records")


def normalize_payments(df: pd.DataFrame):

    df["payments"] = df["payments"].apply(unpack_payments)
    df = df.explode("payments")
    df = df.reset_index(drop=True)
    df = pd.concat(
        (df, pd.json_normalize(df["payments"])),
        axis=1,
    )

    df = df.drop(columns="payments")

    df["pay_date"] = pd.to_datetime(df["pay_date"])
    df["month_end"] = round_to_month_end(df["pay_date"])
    return truncate_past_dates(df)


def get_recommended_bonds(bonds: pd.DataFrame, monthly_bag: pd.DataFrame):

    bonds_last_payment = bonds.sort_values(
        by="pay_val", ascending=False
    ).drop_duplicates(subset="ISIN", keep="first")
    bonds_last_payment.loc[:, "month_end"] = bonds_last_payment[
        "pay_date"
    ] + pd.offsets.MonthEnd(0)

    merged_df = bonds_last_payment.merge(monthly_bag, on="month_end")
    filtered_df = merged_df.loc[
        merged_df["total_pay_val"] <= monthly_bag.mean().values[0]
    ]

    monthly_bag = monthly_bag.reset_index()
    last_month_end = monthly_bag["month_end"].max()

    extra_bonds = bonds_last_payment.loc[
        bonds_last_payment["month_end"] > last_month_end
    ].copy()

    if not extra_bonds.empty:
        extra_bonds.loc[:, "total_pay_val"] = 0

        final_df = pd.concat([filtered_df, extra_bonds], ignore_index=True)
    else:
        final_df = filtered_df.copy()

    final_df.drop(["total_pay_val"], axis=1, inplace=True)
    final_df = final_df.sort_values(by="pay_date", ascending=True)

    return final_df
