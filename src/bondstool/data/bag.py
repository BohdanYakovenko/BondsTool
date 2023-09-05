import numpy as np
import pandas as pd
from bondstool.utils import MAP_HEADINGS, split_dataframe

OVDP_BAG_PATH = "data/ovdp_input_data.xlsx"


def verify_excel_file(file_path):
    df = pd.read_excel(file_path)

    expected_columns = [
        "ISIN",
        "Кілть в портфелі",
        "Загальна сума придбання",
        "Податок на прибуток ЮО (ПнПр)",
    ]
    missing_columns = set(expected_columns) - set(df.columns)

    if missing_columns:
        error_message = (
            f"The Excel file is missing the following columns: "
            f"{', '.join(missing_columns)}"
        )
        raise ValueError(error_message)

    if df.isna().any().any():
        raise ValueError("Warning: The Excel file contains empty cells.")

    expected_types = [object, np.int64, (np.int64, float), (np.int64, float)]

    for column_name, expected_type in zip(expected_columns, expected_types):
        column_type = df[column_name].dtype

        if not isinstance(expected_type, tuple):
            expected_type = (expected_type,)

        if column_type not in expected_type:
            raise ValueError(
                f"Warning: Column '{column_name}' has incorrect data type."
            )

    return df


def read_bag_info():

    bag = verify_excel_file(OVDP_BAG_PATH)

    map_headings = {
        "Кілть в портфелі": "quantity",
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
                "exchange_rate",
            ]
        ],
        how="left",
        on="ISIN",
    )
    bag["total_pay_val"] = bag["pay_val"] * bag["quantity"] * bag["exchange_rate"]

    return bag


def get_payment_schedule(bag: pd.DataFrame):

    bag = bag.sort_values(by="pay_date", ascending=True)

    bag["total_pay_val"] = bag["total_pay_val"] * bag["exchange_rate"]

    bag = bag.drop(
        columns=[
            "quantity",
            "expenditure",
            "tax",
            "pay_val",
            "month_end",
            "exchange_rate",
        ]
    )

    bag["pay_date"] = pd.to_datetime(bag["pay_date"]).dt.strftime("%d-%m-%Y")
    bag["total_pay_val"] = bag["total_pay_val"].round(2)

    actual, historic = split_dataframe(bag)

    map_headings = {
        "type": "Вид",
        "currency": "Валюта",
        "pay_date": "Дата",
        "total_pay_val": "Сума, UAH",
    }

    actual = actual.rename(columns=map_headings)

    return actual


def analyse_bag(bag: pd.DataFrame):
    bag = bag.copy()

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
    sum_row.at[0, "profitability"] = (
        sum_row.at[0, "profit after tax"] / sum_row.at[0, "expenditure"] * 100
    )

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
