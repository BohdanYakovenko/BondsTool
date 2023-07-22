import pandas as pd
from bondstool.utils import round_to_month_end


def payments_by_month(df: pd.DataFrame, pay_col="total_pay_val"):

    return df.groupby(["month_end"])[[pay_col]].sum()


def fill_missing_months(df: pd.DataFrame):

    period_index = pd.period_range(df.index.min(), df.index.max(), freq="M")
    period_index = round_to_month_end(period_index.to_timestamp())

    filled_df = pd.DataFrame(index=pd.Index(period_index, name=df.index.name)).join(df)
    filled_df = filled_df.fillna(0.0)
    return filled_df


def calc_potential_payments(
    trading_bonds: pd.DataFrame,
    amounts: tuple,
    bag_payments: pd.DataFrame,
    isin_df: pd.DataFrame,
):
    for isin, amount in zip(isin_df["ISIN"].values, amounts):
        mask = trading_bonds["ISIN"] == isin
        trading_bonds.loc[mask, "total_pay_val"] = (
            trading_bonds.loc[mask, "pay_val"] * amount
        )

    potential_payments = payments_by_month(trading_bonds, pay_col="total_pay_val")

    df = pd.concat(
        (bag_payments, potential_payments)
        # (bag_payments["total_pay_val"], potential_payments["total_pay_val"])
    )
    # df = payments_by_month(df.to_frame("total_pay_val"))
    df = payments_by_month(df)
    # TODO: omit if filling is not needed
    df = fill_missing_months(df)
    return df
