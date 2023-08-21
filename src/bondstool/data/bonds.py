import pandas as pd
import requests
from bondstool.utils import round_to_month_end, truncate_past_dates

BONDS_URL = "https://bank.gov.ua/depo_securities?json"


def get_bonds_info():

    json = requests.get(url=BONDS_URL).text
    bonds = pd.read_json(json)
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


def create_payments_table(row):
    normalized_data = row["payments"]
    payment_df = pd.DataFrame(normalized_data)
    payment_df["ISIN"] = row["ISIN"]
    return payment_df
