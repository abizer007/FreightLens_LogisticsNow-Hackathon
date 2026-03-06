"""
Executive Dashboard: top metrics and charts.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from modules import insights_engine


def render(
    merged: pd.DataFrame,
    metrics: Optional[Dict[str, Any]] = None,
    insights_summary: Optional[List[Dict[str, Any]]] = None,
    carrier_risk: Optional[pd.DataFrame] = None,
    delay_trends: Optional[pd.DataFrame] = None,
) -> None:
    """Render Executive Dashboard with metrics and charts."""
    if merged.empty:
        st.info("No data to display.")
        return

    # Top metrics
    total_shipments = len(merged)
    high_risk = (merged["Risk_Level"] == "High").sum()
    critical = (merged["Risk_Level"] == "Critical").sum()
    total_exposure = merged["Invoice_Difference"].sum()
    pod_pct = insights_engine.pod_compliance_rate(merged)

    st.subheader("Operational Overview")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Shipments", total_shipments)
    col2.metric("High Risk Shipments", int(high_risk))
    col3.metric("Critical Shipments", int(critical))
    col4.metric("Total Financial Exposure ₹", f"{int(total_exposure):,}")
    col5.metric("POD Compliance %", f"{pod_pct:.1f}%")
    st.divider()

    # Risk distribution
    st.subheader("Risk Distribution")
    fig_risk = px.pie(
        merged,
        names="Risk_Level",
        title="Shipment Risk Breakdown",
        color="Risk_Level",
        color_discrete_map={
            "Critical": "darkred",
            "High": "red",
            "Medium": "orange",
            "Low": "green",
        },
    )
    st.plotly_chart(fig_risk, use_container_width=True)

    # Carrier risk ranking
    if carrier_risk is not None and not carrier_risk.empty:
        st.subheader("Carrier Risk Ranking")
        fig_carrier = px.bar(
            carrier_risk.head(15),
            x="Transport_Company",
            y="Mean_Risk_Score",
            color="Mean_Risk_Score",
            title="Top carriers by mean risk score",
        )
        st.plotly_chart(fig_carrier, use_container_width=True)

    # Delay distribution
    if delay_trends is not None and not delay_trends.empty:
        st.subheader("Delay Distribution")
        fig_delay = px.bar(
            delay_trends,
            x="Month",
            y="mean",
            title="Average delivery delay by month",
            labels={"mean": "Avg delay (days)", "Month": "Month"},
        )
        st.plotly_chart(fig_delay, use_container_width=True)
    else:
        st.subheader("Delay Distribution")
        delay_series = merged.get("Delivery_Delay_Days", pd.Series())
        if not delay_series.empty:
            fig_delay = px.histogram(
                merged,
                x="Delivery_Delay_Days",
                nbins=20,
                title="Delivery delay distribution",
            )
            st.plotly_chart(fig_delay, use_container_width=True)

    # Financial risk breakdown (by risk level)
    st.subheader("Financial Risk Breakdown")
    breakdown = merged.groupby("Risk_Level")["Invoice_Difference"].sum().reset_index()
    if not breakdown.empty:
        fig_fin = px.bar(
            breakdown,
            x="Risk_Level",
            y="Invoice_Difference",
            color="Risk_Level",
            title="Invoice discrepancy by risk level",
            labels={"Invoice_Difference": "Amount ₹", "Risk_Level": "Risk Level"},
        )
        st.plotly_chart(fig_fin, use_container_width=True)

    # Auto investigation summary
    st.subheader("Auto Investigation Summary")
    summary = insights_summary or insights_engine.auto_investigation_summary(merged)
    for item in summary:
        st.info(item.get("message", str(item)))
