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


def get_recommended_bonds(bonds: pd.DataFrame, monthly_bag: pd.DataFrame):

    bonds_last_payment = bonds.sort_values(
        by="pay_val", ascending=False
    ).drop_duplicates(subset="ISIN", keep="first")
    bonds_last_payment.loc[:, "month_end"] = bonds_last_payment[
        "pay_date"
    ] + pd.offsets.MonthEnd(0)

    merged_df = bonds_last_payment.merge(monthly_bag, on="month_end")
    filtered_df = merged_df[merged_df["total_pay_val"] <= monthly_bag.mean().values[0]]

    monthly_bag = monthly_bag.reset_index()
    last_month_end = monthly_bag["month_end"].max()
    extra_bonds = bonds_last_payment[
        bonds_last_payment["month_end"] > last_month_end
    ].copy()
    extra_bonds["total_pay_val"] = 0

    final_df = pd.concat([filtered_df, extra_bonds], ignore_index=True)
    final_df.drop(["total_pay_val", "cpcode_cfi", "emit_okpo"], axis=1, inplace=True)

    return final_df
