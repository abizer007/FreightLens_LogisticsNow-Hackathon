"""
Fraud & Compliance: flagged shipments and risk tables.
"""

from typing import Optional

import pandas as pd
import streamlit as st

from modules import fraud_detection


def render(
    merged: pd.DataFrame,
    fraud_flags: Optional[pd.DataFrame] = None,
) -> None:
    """Render Fraud & Compliance page."""
    if merged.empty:
        st.info("No data to display.")
        return

    if fraud_flags is None or (isinstance(fraud_flags, pd.DataFrame) and fraud_flags.empty):
        fraud_flags = fraud_detection.run_fraud_detection(merged)

    st.subheader("Flagged Shipments")
    if fraud_flags is not None and not fraud_flags.empty:
        st.dataframe(fraud_flags, use_container_width=True, height=250)
        flagged_ids = fraud_flags["Shipment_ID"].tolist()
        detail = merged[merged["Shipment_ID"].isin(flagged_ids)]
        if not detail.empty:
            st.subheader("Flagged Shipment Details")
            st.dataframe(detail, use_container_width=True, height=350)
    else:
        st.success("No shipments flagged for fraud.")

    st.subheader("Duplicate Invoices")
    dup = fraud_detection.detect_duplicate_invoices(merged)
    if not dup.empty:
        st.dataframe(dup, use_container_width=True, height=200)
    else:
        st.write("No duplicate invoices detected.")

    st.subheader("Missing POD or Signature")
    pod_risk = merged[
        (merged.get("Missing_Signature", False)) | (merged.get("POD_Missing", False))
    ]
    if not pod_risk.empty:
        st.dataframe(pod_risk, use_container_width=True, height=200)
    else:
        st.write("No missing POD or signature.")
