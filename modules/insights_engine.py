"""
Insights for dashboards: carrier/driver/lane risk, heatmap, delay trends,
POD compliance, repeated invoice patterns, suspicious carriers, auto investigation summary.
"""

from typing import Any, Dict, List, Optional

import pandas as pd


def carrier_risk_score(merged: pd.DataFrame) -> pd.DataFrame:
    """Aggregate risk (mean and max) per Transport_Company."""
    if "Transport_Company" not in merged.columns or "Risk_Score" not in merged.columns:
        return pd.DataFrame()
    return (
        merged.groupby("Transport_Company")
        .agg(
            Shipment_Count=("Shipment_ID", "count"),
            Mean_Risk_Score=("Risk_Score", "mean"),
            Max_Risk_Score=("Risk_Score", "max"),
        )
        .reset_index()
        .sort_values("Mean_Risk_Score", ascending=False)
    )


def driver_risk_score(merged: pd.DataFrame) -> pd.DataFrame:
    """Aggregate risk per Driver_Name."""
    if "Driver_Name" not in merged.columns or "Risk_Score" not in merged.columns:
        return pd.DataFrame()
    return (
        merged.groupby("Driver_Name")
        .agg(
            Shipment_Count=("Shipment_ID", "count"),
            Mean_Risk_Score=("Risk_Score", "mean"),
            Max_Risk_Score=("Risk_Score", "max"),
        )
        .reset_index()
        .sort_values("Mean_Risk_Score", ascending=False)
    )


def lane_risk_score(merged: pd.DataFrame) -> pd.DataFrame:
    """Aggregate risk per lane (Origin -> Destination)."""
    if "Origin" not in merged.columns or "Destination" not in merged.columns:
        return pd.DataFrame()
    merged = merged.copy()
    merged["Lane"] = merged["Origin"].astype(str) + " → " + merged["Destination"].astype(str)
    return (
        merged.groupby("Lane")
        .agg(
            Shipment_Count=("Shipment_ID", "count"),
            Mean_Risk_Score=("Risk_Score", "mean"),
            Total_Invoice_Diff=("Invoice_Difference", "sum"),
        )
        .reset_index()
        .sort_values("Mean_Risk_Score", ascending=False)
    )


def financial_exposure_heatmap_data(merged: pd.DataFrame) -> pd.DataFrame:
    """Exposure by lane or carrier for heatmap (pivot-style)."""
    if merged.empty or "Invoice_Difference" not in merged.columns:
        return pd.DataFrame()
    df = merged.copy()
    df["Lane"] = df["Origin"].astype(str) + " → " + df["Destination"].astype(str)
    return (
        df.groupby(["Transport_Company", "Lane"])["Invoice_Difference"]
        .sum()
        .reset_index()
    )


def repeated_invoice_patterns(merged: pd.DataFrame) -> pd.DataFrame:
    """Same Invoice_ID or same Total_Invoice_Amount across multiple shipments (for fraud)."""
    if "Invoice_ID" not in merged.columns:
        return pd.DataFrame()
    dup_id = merged[merged.duplicated("Invoice_ID", keep=False)]
    if dup_id.empty:
        return pd.DataFrame()
    return dup_id[["Shipment_ID", "Invoice_ID", "Total_Invoice_Amount", "Transport_Company"]].drop_duplicates()


def suspicious_carrier_detection(merged: pd.DataFrame) -> pd.DataFrame:
    """Carriers with high mismatch rate, repeated missing PODs, or high delay rate."""
    if "Transport_Company" not in merged.columns:
        return pd.DataFrame()
    agg = merged.groupby("Transport_Company").agg(
        Shipments=("Shipment_ID", "count"),
        Mismatch_Count=("Invoice_Difference", lambda s: (s > 100).sum()),
        Missing_POD_Count=("POD_Missing", "sum"),
        Mean_Delay=("Delivery_Delay_Days", "mean"),
        Mean_Risk=("Risk_Score", "mean"),
    ).reset_index()
    agg["Mismatch_Rate"] = agg["Mismatch_Count"] / agg["Shipments"].replace(0, 1)
    suspicious = agg[
        (agg["Mismatch_Rate"] > 0.3)
        | (agg["Missing_POD_Count"] >= 2)
        | (agg["Mean_Delay"] > 3)
    ].sort_values("Mean_Risk", ascending=False)
    return suspicious


def shipment_delay_trends(merged: pd.DataFrame) -> pd.DataFrame:
    """Delay distribution over time or by lane."""
    if "Delivery_Delay_Days" not in merged.columns:
        return pd.DataFrame()
    df = merged.copy()
    if "Dispatch_Date" in df.columns:
        df["Dispatch_Date"] = pd.to_datetime(df["Dispatch_Date"], errors="coerce")
        df["Month"] = df["Dispatch_Date"].dt.to_period("M").astype(str)
    else:
        df["Month"] = "Unknown"
    return (
        df.groupby("Month")["Delivery_Delay_Days"]
        .agg(["mean", "max", "count"])
        .reset_index()
    )


def pod_compliance_rate(merged: pd.DataFrame) -> float:
    """Percentage of shipments with POD (Status == Delivered)."""
    if merged.empty or "Status" not in merged.columns:
        return 0.0
    delivered = (merged["Status"] == "Delivered").sum()
    return 100.0 * delivered / len(merged)


def auto_investigation_summary(merged: pd.DataFrame) -> List[Dict[str, Any]]:
    """Structured list of top issues for dashboard (by risk level, financial exposure)."""
    summary: List[Dict[str, Any]] = []
    if merged.empty:
        return summary
    critical = (merged["Risk_Level"] == "Critical").sum()
    high = (merged["Risk_Level"] == "High").sum()
    if critical > 0:
        summary.append({"type": "Critical Risk", "count": int(critical), "message": f"{critical} shipments in Critical risk"})
    if high > 0:
        summary.append({"type": "High Risk", "count": int(high), "message": f"{high} shipments in High risk"})
    exposure = merged["Invoice_Difference"].sum()
    if exposure > 100_000:
        summary.append({"type": "Financial", "count": int(exposure), "message": f"Total financial exposure ₹{int(exposure):,}"})
    if "Delivery_Delay_Days" in merged.columns and merged["Delivery_Delay_Days"].mean() > 2:
        summary.append({"type": "Operational", "count": 0, "message": "Delivery delays exceed service levels"})
    pod_rate = pod_compliance_rate(merged)
    if pod_rate < 90:
        summary.append({"type": "Compliance", "count": round(pod_rate, 1), "message": f"POD compliance at {pod_rate:.1f}%"})
    return summary
