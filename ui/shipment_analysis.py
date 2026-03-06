"""
Shipment Risk Analysis: table, filters, drill-down with structured investigation.
"""

from typing import Optional

import pandas as pd
import streamlit as st


def render(merged: pd.DataFrame) -> None:
    """Render Shipment Risk Analysis page."""
    if merged.empty:
        st.info("No data to display.")
        return

    st.subheader("Shipment Risk Overview")
    risk_filter = st.selectbox(
        "Filter by Risk Level",
        ["All", "Critical", "High", "Medium", "Low"],
    )
    risk_table = merged.sort_values(by="Risk_Score", ascending=False)
    if risk_filter != "All":
        risk_table = risk_table[risk_table["Risk_Level"] == risk_filter]

    display_cols = [
        "Shipment_ID",
        "Origin",
        "Destination",
        "Transport_Company",
        "Driver_Name",
        "Package_Count",
        "Received_Packages",
        "Total_Invoice_Amount",
        "Risk_Level",
        "Recommended_Action",
    ]
    available = [c for c in display_cols if c in risk_table.columns]
    st.dataframe(
        risk_table[available],
        use_container_width=True,
        height=350,
    )
    st.divider()

    st.subheader("Shipment Investigation")
    selected = st.selectbox("Select Shipment", merged["Shipment_ID"].unique())
    shipment = merged[merged["Shipment_ID"] == selected].iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### Shipment Details")
        st.write("Origin:", shipment.get("Origin", ""))
        st.write("Destination:", shipment.get("Destination", ""))
        st.write("Material:", shipment.get("Material", ""))
    with col2:
        st.markdown("### Transport Info")
        st.write("Carrier:", shipment.get("Transport_Company", ""))
        st.write("Driver:", shipment.get("Driver_Name", ""))
        st.write("Vehicle:", shipment.get("Vehicle_Number", ""))
    with col3:
        st.markdown("### Risk Metrics")
        st.write("Risk Level:", shipment.get("Risk_Level", ""))
        st.write("Risk Score:", round(shipment.get("Risk_Score", 0), 2))
        st.write("Delivery Delay:", shipment.get("Delivery_Delay_Days", 0))

    st.markdown("### AI Investigation Summary")
    inv = shipment.get("Investigation")
    if inv and isinstance(inv, dict):
        st.write("**Shipment ID:**", inv.get("Shipment_ID", ""))
        st.write("**Detected Issues:**")
        for issue in inv.get("Detected_Issues", []):
            st.write("-", issue)
        st.write("**Operational Impact:**", inv.get("Operational_Impact", ""))
        st.write("**Financial Risk:** ₹", inv.get("Financial_Risk", 0))
        st.write("**Suggested Action:**", inv.get("Suggested_Action", ""))
    else:
        st.info(str(inv) if inv else "No investigation data.")
