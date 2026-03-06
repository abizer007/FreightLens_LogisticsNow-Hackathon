"""
Weighted risk scoring, four-level classification, and structured investigation.
"""

import logging
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)

# Weights for risk score (plan formula)
W_QTY = 5
W_INVOICE = 3
W_DELAY = 4
W_WEIGHT = 2
W_MISSING_SIGNATURE = 20
W_MISSING_POD = 30

# Risk level thresholds (four levels: Low, Medium, High, Critical)
THRESHOLD_MEDIUM = 25
THRESHOLD_HIGH = 60
THRESHOLD_CRITICAL = 120


def compute_risk_score(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Add Risk_Score and Risk_Level to the reconciled DataFrame.
    Uses scaled invoice difference (column Invoice_Difference_Scaled if present, else Invoice_Difference).
    """
    df = merged.copy()

    qty = df.get("Quantity_Difference", pd.Series(0, index=df.index)).fillna(0)
    inv_raw = df.get("Invoice_Difference", pd.Series(0, index=df.index)).fillna(0)
    inv_cap = 10_000
    inv_scaled = inv_raw.clip(upper=inv_cap)
    delay = df.get("Delivery_Delay_Days", pd.Series(0, index=df.index)).fillna(0)
    weight = df.get("Weight_Difference", pd.Series(0, index=df.index)).fillna(0)
    miss_sig = df.get("Missing_Signature", pd.Series(False, index=df.index)).astype(int)
    miss_pod = df.get("POD_Missing", pd.Series(False, index=df.index)).astype(int)

    df["Risk_Score"] = (
        qty * W_QTY
        + inv_scaled * W_INVOICE / 1000.0
        + delay * W_DELAY
        + weight * W_WEIGHT / 100.0
        + miss_sig * W_MISSING_SIGNATURE
        + miss_pod * W_MISSING_POD
    )

    def _level(score: float) -> str:
        if score >= THRESHOLD_CRITICAL:
            return "Critical"
        if score >= THRESHOLD_HIGH:
            return "High"
        if score >= THRESHOLD_MEDIUM:
            return "Medium"
        return "Low"

    df["Risk_Level"] = df["Risk_Score"].apply(_level)

    # Log high/critical counts
    critical = (df["Risk_Level"] == "Critical").sum()
    high = (df["Risk_Level"] == "High").sum()
    if critical > 0 or high > 0:
        logger.info("Risk scoring: %d Critical, %d High", critical, high)

    return df


def recommend_action(row: pd.Series) -> str:
    """Recommend action for a single shipment row."""
    if row.get("POD_Missing", False):
        return "Request POD confirmation"
    if row.get("Quantity_Difference", 0) > 0:
        return "Verify package count"
    if row.get("Invoice_Difference", 0) > 100:
        return "Investigate invoice mismatch"
    if row.get("Delivery_Delay_Days", 0) > 2:
        return "Review carrier performance"
    return "Auto approve payment"


def add_recommendations(merged: pd.DataFrame) -> pd.DataFrame:
    """Add Recommended_Action column."""
    df = merged.copy()
    df["Recommended_Action"] = df.apply(recommend_action, axis=1)
    return df


def generate_investigation(row: pd.Series) -> Dict[str, Any]:
    """
    Structured investigation for a shipment: Shipment ID, Detected Issues,
    Operational Impact, Financial Risk, Suggested Action.
    """
    issues: List[str] = []
    if row.get("POD_Missing", False):
        issues.append("Missing POD")
    if row.get("Missing_Signature", False):
        issues.append("Missing signature")
    if row.get("Quantity_Difference", 0) > 0:
        issues.append(f"Quantity mismatch: {int(row['Quantity_Difference'])} packages")
    if row.get("Invoice_Difference", 0) > 0:
        issues.append(f"Invoice discrepancy: ₹{int(row['Invoice_Difference'])}")
    if row.get("Delivery_Delay_Days", 0) > 0:
        issues.append(f"Delivery delay: {int(row['Delivery_Delay_Days'])} days")
    if row.get("Weight_Difference", 0) > 0:
        issues.append(f"Weight mismatch: {round(row['Weight_Difference'], 2)} kg")
    if not issues:
        issues.append("No issues detected")

    operational = "High" if (row.get("POD_Missing") or row.get("Quantity_Difference", 0) > 0) else "Low"
    financial = int(row.get("Invoice_Difference", 0))

    return {
        "Shipment_ID": row.get("Shipment_ID", ""),
        "Detected_Issues": issues,
        "Operational_Impact": operational,
        "Financial_Risk": financial,
        "Suggested_Action": row.get("Recommended_Action", "Auto approve payment"),
    }


def add_investigations(merged: pd.DataFrame) -> pd.DataFrame:
    """Add structured investigation dict/list column for UI."""
    df = merged.copy()
    df["Investigation"] = df.apply(generate_investigation, axis=1)
    return df


def run_risk_pipeline(merged: pd.DataFrame) -> pd.DataFrame:
    """Compute risk score, level, recommendations, and investigations."""
    df = compute_risk_score(merged)
    df = add_recommendations(df)
    df = add_investigations(df)
    return df
