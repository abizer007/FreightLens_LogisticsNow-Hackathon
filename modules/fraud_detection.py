"""
Fraud detection: duplicate invoices, repeated driver/carrier anomalies,
suspicious cost inflation, repeated missing PODs. Returns flagged shipments.
"""

import logging
from typing import List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Thresholds
INVOICE_INFLATION_PCT = 0.25  # invoice > expected by 25%
MIN_REPEATED_ANOMALIES = 2
MIN_MISSING_POD_COUNT = 2


def detect_duplicate_invoices(merged: pd.DataFrame) -> pd.DataFrame:
    """Flag shipments with duplicate Invoice_ID."""
    if "Invoice_ID" not in merged.columns:
        return pd.DataFrame()
    dup = merged[merged.duplicated("Invoice_ID", keep=False)]
    if not dup.empty:
        logger.info("Fraud detection: %d rows with duplicate Invoice_ID", len(dup))
    return dup


def detect_repeated_driver_anomalies(merged: pd.DataFrame) -> pd.DataFrame:
    """Flag drivers with multiple high-risk or anomaly rows."""
    if "Driver_Name" not in merged.columns:
        return pd.DataFrame()
    high_risk = merged[merged["Risk_Level"].isin(["High", "Critical"])]
    driver_counts = high_risk.groupby("Driver_Name").size()
    repeated = driver_counts[driver_counts >= MIN_REPEATED_ANOMALIES].index.tolist()
    if not repeated:
        return pd.DataFrame()
    out = merged[merged["Driver_Name"].isin(repeated)]
    logger.info("Fraud detection: %d drivers with repeated anomalies", len(repeated))
    return out


def detect_repeated_carrier_mismatches(merged: pd.DataFrame) -> pd.DataFrame:
    """Flag carriers with multiple invoice/quantity mismatches."""
    if "Transport_Company" not in merged.columns:
        return pd.DataFrame()
    has_mismatch = (merged.get("Invoice_Difference", 0) > 100) | (
        merged.get("Quantity_Difference", 0) > 0
    )
    mismatch_df = merged[has_mismatch]
    carrier_counts = mismatch_df.groupby("Transport_Company").size()
    repeated = carrier_counts[carrier_counts >= MIN_REPEATED_ANOMALIES].index.tolist()
    if not repeated:
        return pd.DataFrame()
    out = merged[merged["Transport_Company"].isin(repeated)]
    logger.info("Fraud detection: %d carriers with repeated mismatches", len(repeated))
    return out


def detect_suspicious_inflation(merged: pd.DataFrame) -> pd.DataFrame:
    """Flag shipments where invoice significantly exceeds expected amount."""
    if "Expected_Amount" not in merged.columns or "Total_Invoice_Amount" not in merged.columns:
        return pd.DataFrame()
    expected = merged["Expected_Amount"].replace(0, float("nan"))
    ratio = merged["Total_Invoice_Amount"] / expected
    flagged = merged[ratio >= (1 + INVOICE_INFLATION_PCT)]
    if not flagged.empty:
        logger.warning("Fraud detection: %d rows with suspicious cost inflation", len(flagged))
    return flagged


def detect_repeated_missing_pod(merged: pd.DataFrame) -> pd.DataFrame:
    """Flag carriers or drivers with multiple missing PODs."""
    missing = merged[merged.get("POD_Missing", False)]
    if missing.empty:
        return pd.DataFrame()
    carrier_missing = missing.groupby("Transport_Company").size()
    driver_missing = missing.groupby("Driver_Name").size()
    bad_carriers = carrier_missing[carrier_missing >= MIN_MISSING_POD_COUNT].index.tolist()
    bad_drivers = driver_missing[driver_missing >= MIN_MISSING_POD_COUNT].index.tolist()
    out = merged[
        merged["Transport_Company"].isin(bad_carriers)
        | merged["Driver_Name"].isin(bad_drivers)
    ]
    if not out.empty:
        logger.info(
            "Fraud detection: %d carriers, %d drivers with repeated missing POD",
            len(bad_carriers),
            len(bad_drivers),
        )
    return out


def run_fraud_detection(merged: pd.DataFrame) -> pd.DataFrame:
    """
    Run all fraud checks and return a structured table of flagged shipments
    with columns: Shipment_ID, Reason, Severity.
    """
    rows: List[dict] = []
    seen: set = set()  # reset each call to avoid duplicate Shipment_IDs in output

    # Duplicate invoices
    dup_inv = detect_duplicate_invoices(merged)
    for _, row in dup_inv.iterrows():
        sid = row.get("Shipment_ID")
        if sid not in seen:
            seen.add(sid)
            rows.append({"Shipment_ID": sid, "Reason": "Duplicate invoice", "Severity": "High"})

    # Repeated driver anomalies
    drv = detect_repeated_driver_anomalies(merged)
    for _, row in drv.iterrows():
        sid = row.get("Shipment_ID")
        if sid not in seen:
            seen.add(sid)
            rows.append({"Shipment_ID": sid, "Reason": "Driver repeated anomalies", "Severity": "Medium"})

    # Repeated carrier mismatches
    carr = detect_repeated_carrier_mismatches(merged)
    for _, row in carr.iterrows():
        sid = row.get("Shipment_ID")
        if sid not in seen:
            seen.add(sid)
            rows.append({"Shipment_ID": sid, "Reason": "Carrier repeated mismatches", "Severity": "Medium"})

    # Suspicious inflation
    infl = detect_suspicious_inflation(merged)
    for _, row in infl.iterrows():
        sid = row.get("Shipment_ID")
        if sid not in seen:
            seen.add(sid)
            rows.append({"Shipment_ID": sid, "Reason": "Suspicious cost inflation", "Severity": "High"})

    # Repeated missing POD
    pod = detect_repeated_missing_pod(merged)
    for _, row in pod.iterrows():
        sid = row.get("Shipment_ID")
        if sid not in seen:
            seen.add(sid)
            rows.append({"Shipment_ID": sid, "Reason": "Repeated missing POD", "Severity": "Critical"})

    if rows:
        logger.info("Fraud detection: %d shipments flagged", len(rows))
    return pd.DataFrame(rows)
