import pandas as pd
from bondstool.utils import MAP_HEADINGS, split_dataframe

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
        bonds[
            [
                "ISIN",
                "pay_date",
                "pay_val",
                "month_end",
                "type",
                "currency",
            ]
        ],
        how="left",
        on="ISIN",
    )
    bag["total_pay_val"] = bag["pay_val"] * bag["quantity"]

    return bag


def analyse_bag(bag: pd.DataFrame):
    bag = bag.copy()

    bag["expected return"] = bag["expected return"] * bag["exchange_rate"]

    bag["profit before tax"] = bag["expected return"] - bag["expenditure"]
    bag["profit after tax"] = bag["profit before tax"] * (1 - bag["tax"])
    bag["profit per bond"] = bag["profit after tax"] / bag["quantity"]
    bag["profitability"] = bag["profit after tax"] / bag["expenditure"] * 100

    return bag


def get_sums_row(bag: pd.DataFrame):

    assigned_columns = [
        "quantity",
        "expenditure",
        "expected return",
        "profit before tax",
        "profit after tax",
    ]

    column_sums = bag[assigned_columns].sum()

    sum_row = pd.DataFrame([column_sums], columns=assigned_columns)
    sum_row.at[0, "ISIN"] = "Разом"

    return sum_row


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

    sum_row = get_sums_row(actual)

    actual.loc[actual.shape[0]] = None
    combined_actual = pd.concat([actual, sum_row], ignore_index=True)
    combined_actual.loc[combined_actual.shape[0]] = None

    combined_actual["pay_date"] = pd.to_datetime(
        combined_actual["pay_date"]
    ).dt.strftime("%d-%m-%Y")

    columns_to_round = [
        "expenditure",
        "expected return",
        "profit before tax",
        "profit after tax",
        "profit per bond",
        "profitability",
    ]

    combined_actual.loc[:, columns_to_round] = combined_actual[columns_to_round].round(
        2
    )

    historic_copy = historic.copy()

    historic_copy.loc[:, ["pay_date", "tax", "expected return"]] = [
        "Погашена",
        None,
        None,
    ]

    combined_bag = pd.concat(
        [combined_actual, historic_copy], ignore_index=True, sort=False
    )
    combined_bag = combined_bag.rename(columns=MAP_HEADINGS)

    return combined_bag
