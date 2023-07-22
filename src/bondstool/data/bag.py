import pandas as pd

OVDP_BAG_PATH = "data/ovdp_bag_31.05.23.xlsx"
ISIN_PREFIX = "UA4000"


def read_bag_info():

    bag = pd.read_excel(OVDP_BAG_PATH)
    bag = bag.loc[1:10].reset_index(drop=True)
    bag["ISIN"] = ISIN_PREFIX + bag["ISIN"].astype("str")

    map_headings = {"Кіл-ть в портфелі": "quantity"}

    bag = bag.rename(columns=map_headings)

    return bag


def merge_bonds_info(bag: pd.DataFrame, bonds: pd.DataFrame):

    bag = bag.merge(
        bonds[["ISIN", "pay_date", "pay_val", "month_end"]],
        how="left",
        on="ISIN",
    )
    bag["total_pay_val"] = bag["pay_val"] * bag["quantity"]

    return bag
