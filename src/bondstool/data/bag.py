import pandas as pd
from bondstool.utils import split_dataframe

OVDP_BAG_PATH = "data/ovdp_bag_31.05.23.xlsx"
ISIN_PREFIX = "UA4000"


def read_bag_info():

    bag = pd.read_excel(OVDP_BAG_PATH)
    bag = bag.loc[1:10].reset_index(drop=True)
    # bag["ISIN"] = ISIN_PREFIX + bag["ISIN"].astype("str")

    bag = bag.drop(
        columns=[
            "Тип",
            "Дата погашеня",
            "Очікувана сума погашення",
            "Інвестиційний результат очікуваний без податку на прибуток",
            "Інвестиційний результат очікуваний за мінусом ПнПр",
        ]
    )

    map_headings = {
        "Кіл-ть в портфелі": "quantity",
        "Загальна сума придбання": "expenditure",
        "Податок на прибуток ЮО (ПнПр)": "tax",
    }

    bag = bag.rename(columns=map_headings)

    return bag


def merge_bonds_info(bag: pd.DataFrame, bonds: pd.DataFrame):

    bag = bag.merge(
        bonds[["ISIN", "pay_date", "pay_val", "month_end", "type"]],
        how="left",
        on="ISIN",
    )
    bag["total_pay_val"] = bag["pay_val"] * bag["quantity"]

    return bag


def analyse_bag(bag: pd.DataFrame):
    bag = bag.copy()

    bag["profit before tax"] = bag["expected return"] - bag["expenditure"]
    bag["profit after tax"] = bag["profit before tax"] * (1 - bag["tax"])
    bag["profit per bond"] = bag["profit after tax"] / bag["quantity"]
    bag["profitability"] = bag["profit after tax"] / bag["expenditure"] * 100

    return bag


def format_bag(bag: pd.DataFrame):

    bag["expected return"] = bag.groupby("ISIN")["total_pay_val"].transform("sum")
    bag = bag.drop(
        columns=[
            "pay_val",
            "month_end",
            "total_pay_val",
        ]
    )
    bag = bag.sort_values(by="pay_date", ascending=True).drop_duplicates(
        subset="ISIN", keep="last"
    )

    actual, historic = split_dataframe(bag)

    actual = analyse_bag(actual)

    actual["pay_date"] = pd.to_datetime(actual["pay_date"]).dt.strftime("%d-%m-%Y")

    columns_to_round = [
        "expenditure",
        "expected return",
        "profit before tax",
        "profit after tax",
        "profit per bond",
        "profitability",
    ]

    actual.loc[:, columns_to_round] = actual[columns_to_round].round(2)

    combined_bag = pd.concat([actual, historic], ignore_index=True, sort=False)

    return combined_bag
