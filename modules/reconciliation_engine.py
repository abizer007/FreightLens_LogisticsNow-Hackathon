"""
Merge LR, POD, and Invoice documents and detect discrepancies.
"""

from typing import Optional

import pandas as pd


def merge_documents(
    lr: pd.DataFrame,
    pod: pd.DataFrame,
    invoice: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge LR, POD, and Invoice DataFrames on Shipment_ID (left joins).
    Returns single merged DataFrame with standard column names.
    """
    merged = lr.merge(pod, on="Shipment_ID", how="left")
    merged = merged.merge(invoice, on="Shipment_ID", how="left")
    return merged


def detect_discrepancies(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Add discrepancy columns to merged DataFrame:
    quantity mismatch, weight mismatch, invoice mismatch,
    missing POD, missing signature, delivery delay.
    Returns merged with new columns.
    """
    df = merged.copy()

    # Quantity mismatch
    if "Package_Count" in df.columns and "Received_Packages" in df.columns:
        df["Quantity_Difference"] = (
            df["Package_Count"].fillna(0).astype(float)
            - df["Received_Packages"].fillna(0).astype(float)
        ).abs()
    else:
        df["Quantity_Difference"] = 0

    # Expected amount (LR) vs invoice
    if "Freight" in df.columns:
        df["Expected_Amount"] = (
            df["Freight"].fillna(0)
            + df.get("Loading_Charges", pd.Series(0, index=df.index)).fillna(0)
            + df.get("Unloading_Charges", pd.Series(0, index=df.index)).fillna(0)
        )
    if "Total_Invoice_Amount" in df.columns:
        df["Invoice_Difference"] = (
            df["Expected_Amount"].fillna(0) - df["Total_Invoice_Amount"].fillna(0)
        ).abs()
    else:
        df["Invoice_Difference"] = 0.0

    # Weight mismatch
    if "Weight_KG" in df.columns and "Charged_Weight" in df.columns:
        df["Weight_Difference"] = (
            df["Weight_KG"].fillna(0) - df["Charged_Weight"].fillna(0)
        ).abs()
    else:
        df["Weight_Difference"] = 0.0

    # Delivery delay
    df["Dispatch_Date"] = pd.to_datetime(df["Dispatch_Date"], errors="coerce")
    df["Delivery_Date"] = pd.to_datetime(df["Delivery_Date"], errors="coerce")
    df["Delivery_Delay_Days"] = (
        df["Delivery_Date"] - df["Dispatch_Date"]
    ).dt.days
    df["Delivery_Delay_Days"] = df["Delivery_Delay_Days"].fillna(0).clip(lower=0)

    # Missing signature and POD
    df["Missing_Signature"] = (df.get("Signature_Available", pd.Series("", index=df.index)) == "No")
    df["POD_Missing"] = (df.get("Status", pd.Series("", index=df.index)) != "Delivered")

    return df
