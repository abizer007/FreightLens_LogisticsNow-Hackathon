"""
Data validation pipeline for logistics datasets.
Flags and normalizes unrealistic values; logs warnings.
"""

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Thresholds for realistic logistics bounds
FREIGHT_MIN = 0
INVOICE_DIFF_CAP = 100_000  # cap for scoring; flag if above
DELAY_DAYS_MIN = 0
DELAY_DAYS_MAX = 90  # flag if beyond
WEIGHT_MISMATCH_PCT = 0.5  # flag if weight diff > 50% of Weight_KG
PACKAGE_RECEIVED_MAX_PCT = 1.0  # received should not exceed dispatched


def _ensure_numeric(series: pd.Series, name: str) -> pd.Series:
    """Coerce to numeric; invalid become NaN."""
    return pd.to_numeric(series, errors="coerce")


def validate_and_normalize_merged(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Run validation rules on the merged LR-POD-Invoice DataFrame.
    Adds validation flag columns and normalizes values for downstream use.
    Logs warnings for violations.
    """
    df = merged.copy()

    # 1. Freight and related charges must be positive
    for col in ["Freight", "Loading_Charges", "Unloading_Charges"]:
        if col not in df.columns:
            continue
        s = _ensure_numeric(df[col], col)
        neg = (s < FREIGHT_MIN).sum()
        if neg > 0:
            logger.warning("Validation: %s negative or non-numeric in %d rows", col, neg)
        df[f"_valid_{col}"] = s >= FREIGHT_MIN
        df[col] = s.clip(lower=FREIGHT_MIN)

    # 2. Invoice difference threshold cap (flag only; risk_engine does its own scaling)
    if "Invoice_Difference" in df.columns:
        inv_diff = _ensure_numeric(df["Invoice_Difference"], "Invoice_Difference")
        over_cap = (inv_diff > INVOICE_DIFF_CAP).sum()
        if over_cap > 0:
            logger.warning(
                "Validation: Invoice_Difference over cap %s in %d rows",
                INVOICE_DIFF_CAP,
                over_cap,
            )
        df["_invoice_diff_over_cap"] = inv_diff > INVOICE_DIFF_CAP
    else:
        df["Invoice_Difference"] = pd.Series(0.0, index=df.index)

    # 3. Delivery delay reasonable bounds
    if "Delivery_Delay_Days" in df.columns:
        delay = _ensure_numeric(df["Delivery_Delay_Days"], "Delivery_Delay_Days")
        delay = delay.fillna(0)
        out_of_bounds = ((delay < DELAY_DAYS_MIN) | (delay > DELAY_DAYS_MAX)).sum()
        if out_of_bounds > 0:
            logger.warning(
                "Validation: Delivery_Delay_Days outside [%s, %s] in %d rows",
                DELAY_DAYS_MIN,
                DELAY_DAYS_MAX,
                out_of_bounds,
            )
        df["_delay_out_of_bounds"] = (delay < DELAY_DAYS_MIN) | (delay > DELAY_DAYS_MAX)
        df["Delivery_Delay_Days"] = delay.clip(lower=DELAY_DAYS_MIN, upper=DELAY_DAYS_MAX)
    elif "Delivery_Date" in df.columns and "Dispatch_Date" in df.columns:
        df["Dispatch_Date"] = pd.to_datetime(df["Dispatch_Date"], errors="coerce")
        df["Delivery_Date"] = pd.to_datetime(df["Delivery_Date"], errors="coerce")
        delay = (df["Delivery_Date"] - df["Dispatch_Date"]).dt.days
        delay = delay.fillna(0).clip(lower=DELAY_DAYS_MIN, upper=DELAY_DAYS_MAX)
        df["Delivery_Delay_Days"] = delay

    # 4. Weight mismatch tolerance (flag only; do not overwrite Weight_Difference if already set)
    if "Weight_KG" in df.columns and "Charged_Weight" in df.columns:
        w_kg = _ensure_numeric(df["Weight_KG"], "Weight_KG")
        w_ch = _ensure_numeric(df["Charged_Weight"], "Charged_Weight")
        w_diff = (w_kg - w_ch).abs()
        if "Weight_Difference" not in df.columns:
            df["Weight_Difference"] = w_diff
        threshold = (w_kg * WEIGHT_MISMATCH_PCT).fillna(0)
        df["_weight_mismatch_high"] = w_diff > threshold
        if df["_weight_mismatch_high"].sum() > 0:
            logger.warning(
                "Validation: Weight mismatch over tolerance in %d rows",
                int(df["_weight_mismatch_high"].sum()),
            )
    elif "Weight_Difference" not in df.columns:
        df["Weight_Difference"] = pd.Series(0.0, index=df.index)

    # 5. Package count consistency (received <= dispatched) (flag only; do not overwrite Quantity_Difference)
    if "Package_Count" in df.columns and "Received_Packages" in df.columns:
        pkg = _ensure_numeric(df["Package_Count"], "Package_Count")
        recv = _ensure_numeric(df["Received_Packages"], "Received_Packages")
        if "Quantity_Difference" not in df.columns:
            df["Quantity_Difference"] = (pkg - recv.fillna(pkg)).abs()
        inconsistent = (recv > pkg).sum()
        if inconsistent > 0:
            logger.warning(
                "Validation: Received_Packages > Package_Count in %d rows",
                int(inconsistent),
            )
        df["_package_inconsistent"] = recv > pkg
    elif "Quantity_Difference" not in df.columns:
        df["Quantity_Difference"] = pd.Series(0, index=df.index)

    # Aggregate validation flag for downstream
    flag_cols = [c for c in df.columns if c.startswith("_valid_") or c.startswith("_")]
    df["_validation_flagged"] = df[[c for c in flag_cols if c in df.columns]].any(axis=1)

    return df


def get_validation_flags(merged: pd.DataFrame) -> List[str]:
    """Return list of column names used as validation flags (for dropping before analytics)."""
    return [c for c in merged.columns if c.startswith("_")]
