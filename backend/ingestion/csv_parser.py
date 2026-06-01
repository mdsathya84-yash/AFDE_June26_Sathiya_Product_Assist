import hashlib
import pandas as pd
from pathlib import Path
from typing import Tuple


def _doc_id(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()[:32]


def parse_csv(csv_path: str | Path) -> Tuple[list[str], list[dict], list[str]]:
    """
    Returns (documents, metadatas, ids) for all rows + aggregate summaries.
    IDs are deterministic SHA-256 hashes to prevent duplicate ingestion.
    """
    df = pd.read_csv(csv_path)
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.strftime("%Y-%m")

    documents: list[str] = []
    metadatas: list[dict] = []
    ids: list[str] = []

    # --- Row-level documents ---
    for _, row in df.iterrows():
        text = (
            f"On {row['Date'].strftime('%Y-%m-%d')}, {row['Product_Name']} "
            f"(ID: {row['Product_ID']}) in the {row['Category']} category sold "
            f"{int(row['Units_Sold'])} units in the {row['Region']} region generating "
            f"${row['Revenue_USD']:.2f} revenue with ${row['Profit_USD']:.2f} profit. "
            f"Marketing spend was ${row['Marketing_Spend_USD']:.2f}. "
            f"Customer rating: {row['Customer_Rating']}/5. "
            f"Returns: {int(row['Returns'])}. "
            f"New customers acquired: {int(row['New_Customers'])}. "
            f"Customer review: \"{row['Review']}\""
        )
        meta = {
            "source_type": "sales_row",
            "product_id": str(row["Product_ID"]),
            "product_name": str(row["Product_Name"]),
            "category": str(row["Category"]),
            "region": str(row["Region"]),
            "date": row["Date"].strftime("%Y-%m-%d"),
            "month": str(row["Month"]),
            "revenue_usd": float(row["Revenue_USD"]),
            "profit_usd": float(row["Profit_USD"]),
            "customer_rating": float(row["Customer_Rating"]),
            "chunk_index": 0,
            "doc_id": _doc_id(text),
        }
        documents.append(text)
        metadatas.append(meta)
        ids.append(_doc_id(text))

    # --- Product aggregates ---
    product_group = df.groupby(["Product_ID", "Product_Name", "Category"]).agg(
        total_revenue=("Revenue_USD", "sum"),
        total_profit=("Profit_USD", "sum"),
        total_units=("Units_Sold", "sum"),
        avg_rating=("Customer_Rating", "mean"),
        total_returns=("Returns", "sum"),
        total_marketing=("Marketing_Spend_USD", "sum"),
    ).reset_index()

    for _, row in product_group.iterrows():
        return_rate = (
            row["total_returns"] / row["total_units"] * 100
            if row["total_units"] > 0 else 0
        )
        roi = (
            row["total_profit"] / row["total_marketing"]
            if row["total_marketing"] > 0 else 0
        )
        text = (
            f"Product Summary for {row['Product_Name']} ({row['Product_ID']}) "
            f"in category {row['Category']}: "
            f"Total revenue ${row['total_revenue']:.2f}, "
            f"total profit ${row['total_profit']:.2f}, "
            f"total units sold {int(row['total_units'])}, "
            f"average customer rating {row['avg_rating']:.2f}/5, "
            f"return rate {return_rate:.1f}%, "
            f"marketing ROI {roi:.2f}x."
        )
        meta = {
            "source_type": "product_summary",
            "product_id": str(row["Product_ID"]),
            "product_name": str(row["Product_Name"]),
            "category": str(row["Category"]),
            "region": None,
            "date": None,
            "month": None,
            "revenue_usd": float(row["total_revenue"]),
            "profit_usd": float(row["total_profit"]),
            "customer_rating": float(row["avg_rating"]),
            "chunk_index": 0,
            "doc_id": _doc_id(text),
        }
        documents.append(text)
        metadatas.append(meta)
        ids.append(_doc_id(text))

    # --- Category aggregates ---
    cat_group = df.groupby("Category").agg(
        total_revenue=("Revenue_USD", "sum"),
        total_profit=("Profit_USD", "sum"),
        total_units=("Units_Sold", "sum"),
        avg_rating=("Customer_Rating", "mean"),
        total_returns=("Returns", "sum"),
    ).reset_index()

    for _, row in cat_group.iterrows():
        return_rate = (
            row["total_returns"] / row["total_units"] * 100
            if row["total_units"] > 0 else 0
        )
        text = (
            f"Category Summary for {row['Category']}: "
            f"Total revenue ${row['total_revenue']:.2f}, "
            f"total profit ${row['total_profit']:.2f}, "
            f"total units {int(row['total_units'])}, "
            f"average rating {row['avg_rating']:.2f}/5, "
            f"return rate {return_rate:.1f}%."
        )
        meta = {
            "source_type": "category_summary",
            "product_id": None,
            "product_name": None,
            "category": str(row["Category"]),
            "region": None,
            "date": None,
            "month": None,
            "revenue_usd": float(row["total_revenue"]),
            "profit_usd": float(row["total_profit"]),
            "customer_rating": float(row["avg_rating"]),
            "chunk_index": 0,
            "doc_id": _doc_id(text),
        }
        documents.append(text)
        metadatas.append(meta)
        ids.append(_doc_id(text))

    # --- Region aggregates ---
    reg_group = df.groupby("Region").agg(
        total_revenue=("Revenue_USD", "sum"),
        total_profit=("Profit_USD", "sum"),
        total_units=("Units_Sold", "sum"),
        avg_rating=("Customer_Rating", "mean"),
        total_returns=("Returns", "sum"),
    ).reset_index()

    for _, row in reg_group.iterrows():
        return_rate = (
            row["total_returns"] / row["total_units"] * 100
            if row["total_units"] > 0 else 0
        )
        text = (
            f"Region Summary for {row['Region']}: "
            f"Total revenue ${row['total_revenue']:.2f}, "
            f"total profit ${row['total_profit']:.2f}, "
            f"total units {int(row['total_units'])}, "
            f"average rating {row['avg_rating']:.2f}/5, "
            f"return rate {return_rate:.1f}%."
        )
        meta = {
            "source_type": "region_summary",
            "product_id": None,
            "product_name": None,
            "category": None,
            "region": str(row["Region"]),
            "date": None,
            "month": None,
            "revenue_usd": float(row["total_revenue"]),
            "profit_usd": float(row["total_profit"]),
            "customer_rating": float(row["avg_rating"]),
            "chunk_index": 0,
            "doc_id": _doc_id(text),
        }
        documents.append(text)
        metadatas.append(meta)
        ids.append(_doc_id(text))

    # --- Monthly trend aggregates ---
    monthly_group = df.groupby("Month").agg(
        total_revenue=("Revenue_USD", "sum"),
        total_profit=("Profit_USD", "sum"),
        total_units=("Units_Sold", "sum"),
        avg_rating=("Customer_Rating", "mean"),
    ).reset_index()

    for _, row in monthly_group.iterrows():
        # Find top product for this month
        month_df = df[df["Month"] == row["Month"]]
        top_product = month_df.groupby("Product_Name")["Revenue_USD"].sum().idxmax()
        text = (
            f"Monthly Summary for {row['Month']}: "
            f"Total revenue ${row['total_revenue']:.2f}, "
            f"total profit ${row['total_profit']:.2f}, "
            f"total units {int(row['total_units'])}, "
            f"average rating {row['avg_rating']:.2f}/5, "
            f"top product by revenue: {top_product}."
        )
        meta = {
            "source_type": "monthly_summary",
            "product_id": None,
            "product_name": None,
            "category": None,
            "region": None,
            "date": None,
            "month": str(row["Month"]),
            "revenue_usd": float(row["total_revenue"]),
            "profit_usd": float(row["total_profit"]),
            "customer_rating": float(row["avg_rating"]),
            "chunk_index": 0,
            "doc_id": _doc_id(text),
        }
        documents.append(text)
        metadatas.append(meta)
        ids.append(_doc_id(text))

    return documents, metadatas, ids
