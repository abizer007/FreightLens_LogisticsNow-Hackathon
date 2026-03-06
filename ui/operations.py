"""
Operational Intelligence: carrier/driver/lane risk, delay trends, POD compliance.
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from modules import insights_engine


def render(
    merged: pd.DataFrame,
    carrier_risk: Optional[pd.DataFrame] = None,
    driver_risk: Optional[pd.DataFrame] = None,
    lane_risk: Optional[pd.DataFrame] = None,
    delay_trends: Optional[pd.DataFrame] = None,
) -> None:
    """Render Operational Intelligence page."""
    if merged.empty:
        st.info("No data to display.")
        return

    if carrier_risk is None or (isinstance(carrier_risk, pd.DataFrame) and carrier_risk.empty):
        carrier_risk = insights_engine.carrier_risk_score(merged)
    if driver_risk is None or (isinstance(driver_risk, pd.DataFrame) and driver_risk.empty):
        driver_risk = insights_engine.driver_risk_score(merged)
    if lane_risk is None or (isinstance(lane_risk, pd.DataFrame) and lane_risk.empty):
        lane_risk = insights_engine.lane_risk_score(merged)
    if delay_trends is None or (isinstance(delay_trends, pd.DataFrame) and delay_trends.empty):
        delay_trends = insights_engine.shipment_delay_trends(merged)
    pod_pct = insights_engine.pod_compliance_rate(merged)

    st.subheader("Carrier Risk Score")
    if not carrier_risk.empty:
        fig = px.bar(
            carrier_risk.head(15),
            x="Transport_Company",
            y="Mean_Risk_Score",
            color="Mean_Risk_Score",
            title="Carrier risk ranking",
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(carrier_risk, use_container_width=True, height=200)
    else:
        st.write("No carrier data.")

    st.subheader("Driver Risk Score")
    if not driver_risk.empty:
        st.dataframe(driver_risk.sort_values("Mean_Risk_Score", ascending=False), use_container_width=True, height=250)
    else:
        st.write("No driver data.")

    st.subheader("Lane Risk Score (Origin → Destination)")
    if not lane_risk.empty:
        st.dataframe(lane_risk.head(20), use_container_width=True, height=250)
    else:
        st.write("No lane data.")

    st.subheader("Shipment Delay Trends")
    if delay_trends is not None and not delay_trends.empty:
        fig_delay = px.bar(
            delay_trends,
            x="Month",
            y="mean",
            title="Average delivery delay by month",
            labels={"mean": "Avg delay (days)"},
        )
        st.plotly_chart(fig_delay, use_container_width=True)
    else:
        st.write("No delay trend data.")

    st.subheader("POD Compliance Rate")
    st.metric("POD Compliance %", f"{pod_pct:.1f}%")
