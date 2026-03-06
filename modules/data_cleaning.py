"""
Dataset cleaning: outlier removal, null handling, numeric validation, realistic bounds.
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Realistic financial bounds (for clipping)
FREIGHT_MAX = 500_000
INVOICE_AMOUNT_MAX = 1_000_000
WEIGHT_KG_MAX = 50_000
PACKAGE_COUNT_MAX = 10_000
DELAY_DAYS_MAX = 90


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a logistics DataFrame: outlier removal, null handling,
    numeric validation, and realistic financial/operational bounds.
    """
    if df is None or df.empty:
        return df

    out = df.copy()

    # Numeric columns that must be non-negative
    amount_cols = [
        "Freight", "Loading_Charges", "Unloading_Charges",
        "Total_LR_Amount", "Total_Invoice_Amount", "Freight_Charge",
        "Fuel_Surcharge", "Tax", "Subtotal", "Expected_Amount",
        "Invoice_Difference", "Weight_KG", "Charged_Weight", "Weight_Difference",
        "Quantity_Difference", "Package_Count", "Received_Packages",
        "Delivery_Delay_Days",
    ]
    for col in amount_cols:
        if col not in out.columns:
            continue
        out[col] = pd.to_numeric(out[col], errors="coerce")
        if col in ("Freight", "Loading_Charges", "Unloading_Charges", "Total_LR_Amount",
                   "Freight_Charge", "Fuel_Surcharge", "Tax", "Subtotal", "Total_Invoice_Amount",
                   "Expected_Amount", "Invoice_Difference"):
            out[col] = out[col].clip(lower=0, upper=INVOICE_AMOUNT_MAX)
        elif col in ("Weight_KG", "Charged_Weight", "Weight_Difference"):
            out[col] = out[col].clip(lower=0, upper=WEIGHT_KG_MAX)
        elif col in ("Package_Count", "Received_Packages", "Quantity_Difference"):
            out[col] = out[col].clip(lower=0, upper=PACKAGE_COUNT_MAX)
        elif col == "Delivery_Delay_Days":
            out[col] = out[col].clip(lower=0, upper=DELAY_DAYS_MAX)

    # Null handling: fill numeric with 0 where it makes sense
    for col in ["Received_Packages", "Quantity_Difference", "Weight_Difference",
                "Invoice_Difference", "Delivery_Delay_Days"]:
        if col in out.columns:
            out[col] = out[col].fillna(0)
    for col in ["Package_Count", "Weight_KG", "Charged_Weight"]:
        if col in out.columns:
            out[col] = out[col].fillna(0)

    # Outlier removal: optional IQR-based for key metrics (do not drop rows by default to preserve traceability; clip instead)
    for col in ["Invoice_Difference", "Delivery_Delay_Days", "Weight_Difference"]:
        if col not in out.columns:
            continue
        q1 = out[col].quantile(0.25)
        q3 = out[col].quantile(0.75)
        iqr = q3 - q1
        if iqr > 0:
            upper = q3 + 1.5 * iqr
            lower = max(0, q1 - 1.5 * iqr)
            clipped = (out[col] > upper).sum() + (out[col] < lower).sum()
            if clipped > 0:
                logger.info("Cleaning: clipped %d outliers for %s", clipped, col)
            out[col] = out[col].clip(lower=lower, upper=upper)

    return out


def strip_validation_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove internal validation prefix columns before passing to UI/analytics."""
    drop = [c for c in df.columns if c.startswith("_")]
    if drop:
        return df.drop(columns=drop, errors="ignore")
    return df
