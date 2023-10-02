import pandas as pd
from bondstool.utils import round_to_month_end


def payments_by_month(df: pd.DataFrame, pay_col="total_pay_val"):
    return df.groupby(["month_end"])[[pay_col]].sum()


def fill_missing_months(df: pd.DataFrame):
    period_index = pd.period_range(
        df.index.min(), df.index.max() + pd.DateOffset(months=1), freq="M"
    )
    period_index = round_to_month_end(period_index.to_timestamp())

    filled_df = pd.DataFrame(index=pd.Index(period_index, name=df.index.name)).join(df)
    filled_df = filled_df.fillna(0.0)
    return filled_df


def calc_potential_payments(
    trading_bonds: pd.DataFrame,
    amounts: list,
    bag_payments: pd.DataFrame,
    isin_df: pd.DataFrame,
):
    for isin, amount in zip(isin_df["ISIN"].values, amounts):
        mask = trading_bonds["ISIN"] == isin
        trading_bonds.loc[mask, "total_pay_val"] = (
            trading_bonds.loc[mask, "pay_val"]
            * amount
            * trading_bonds.loc[mask, "exchange_rate"]
        )

    potential_payments = payments_by_month(trading_bonds, pay_col="total_pay_val")

    df = pd.concat((bag_payments, potential_payments))
    df = payments_by_month(df)

    df = fill_missing_months(df)
    return df


def calculate_profitability(bonds: pd.DataFrame):

    sums = bonds.groupby("ISIN")["pay_val"].sum().reset_index()
    sums.rename(columns={"pay_val": "sum_pay_val"}, inplace=True)

    bonds = bonds.merge(sums, on="ISIN")
    bonds["profitability"] = (
        (bonds["sum_pay_val"] - bonds["nominal"]) / bonds["nominal"] * 100
    )

    return bonds
