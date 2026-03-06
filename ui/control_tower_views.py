"""
LogisticsNow AI Console - Control Tower style views.
All analytics use the existing merged dataframe only.
"""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from modules import fraud_detection
from modules import insights_engine

try:
    from ui.brand_css import BRAND_VALUES_HTML
except Exception:
    BRAND_VALUES_HTML = ""


def _section_header(title: str) -> None:
    st.markdown(f'<p class="ln-section-title">{title}</p>', unsafe_allow_html=True)


def render_control_tower(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Hero dashboard with large metric cards."""
    if merged.empty:
        st.info("No data to display.")
        return
    _section_header("Shipment Metrics")
    total = len(merged)
    high_risk = (merged["Risk_Level"] == "High").sum()
    medium_risk = (merged["Risk_Level"] == "Medium").sum()
    low_risk = (merged["Risk_Level"] == "Low").sum()
    critical = (merged["Risk_Level"] == "Critical").sum()
    financial = merged["Invoice_Difference"].sum()
    avg_delay = merged.get("Delivery_Delay_Days", pd.Series(0, index=merged.index)).fillna(0).mean()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    for col, (label, value, icon) in zip(
        [col1, col2, col3, col4, col5, col6],
        [
            ("Total Shipments", total, "🚚"),
            ("High Risk Shipments", int(high_risk + critical), "⚠"),
            ("Medium Risk Shipments", int(medium_risk), "📦"),
            ("Low Risk Shipments", int(low_risk), "✅"),
            ("Financial Risk Exposure ₹", f"{int(financial):,}", "💰"),
            ("Avg Delivery Delay (days)", f"{avg_delay:.1f}", "⏱"),
        ],
    ):
        with col:
            st.markdown(
                f'<div class="ln-metric-card"><span class="label">{icon} {label}</span><br><span class="value">{value}</span></div>',
                unsafe_allow_html=True,
            )
    st.markdown(BRAND_VALUES_HTML, unsafe_allow_html=True)


def render_shipment_intelligence(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Shipment map (Latitude/Longitude) and Logistics Alert Center."""
    if merged.empty:
        st.info("No data to display.")
        return
    _section_header("Shipment Monitoring Map")
    if "Latitude" in merged.columns and "Longitude" in merged.columns:
        map_df = merged[["Latitude", "Longitude", "Risk_Level", "Shipment_ID"]].dropna(subset=["Latitude", "Longitude"])
        if not map_df.empty:
            color_map = {"Critical": "#c62828", "High": "#c62828", "Medium": "#ef6c00", "Low": "#2e7d32"}
            fig = px.scatter_mapbox(
                map_df,
                lat="Latitude",
                lon="Longitude",
                color="Risk_Level",
                hover_name="Shipment_ID",
                color_discrete_map=color_map,
                zoom=5,
                height=450,
                size_max=15,
            )
            fig.update_layout(
                mapbox_style="carto-positron",
                margin=dict(l=0, r=0, t=0, b=0),
                font=dict(family="Source Sans Pro"),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid Latitude/Longitude in dataset.")
    else:
        st.warning("Latitude and Longitude columns not found in merged data.")

    _section_header("Logistics Alert Center")
    alerts = []
    if merged.get("POD_Missing", pd.Series(False)).any():
        n = merged["POD_Missing"].sum()
        alerts.append(("error", f"Missing POD detected: {int(n)} shipment(s) without proof of delivery."))
    if "Delivery_Delay_Days" in merged.columns and (merged["Delivery_Delay_Days"] > 2).any():
        n = (merged["Delivery_Delay_Days"] > 2).sum()
        alerts.append(("warning", f"Delivery delay above threshold: {int(n)} shipment(s) with delay > 2 days."))
    if merged.get("Invoice_Difference", pd.Series(0)).gt(100).any():
        n = (merged["Invoice_Difference"] > 100).sum()
        alerts.append(("warning", f"Invoice mismatch detected: {int(n)} shipment(s) with significant discrepancy."))
    if merged.get("Quantity_Difference", pd.Series(0)).gt(0).any():
        n = (merged["Quantity_Difference"] > 0).sum()
        alerts.append(("warning", f"Package count mismatch: {int(n)} shipment(s) with quantity discrepancy."))
    if not alerts:
        alerts.append(("success", "No critical alerts. Operations within normal parameters."))
    for level, msg in alerts:
        if level == "error":
            st.error(msg)
        elif level == "warning":
            st.warning(msg)
        else:
            st.success(msg)


def render_carrier_analytics(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Carrier leaderboard and Top Risky / Best Performing charts."""
    if merged.empty:
        st.info("No data to display.")
        return
    carrier_risk = context.get("carrier_risk") if context else None
    if carrier_risk is None or carrier_risk.empty:
        carrier_risk = merged.groupby("Transport_Company").agg(
            Shipment_Count=("Shipment_ID", "count"),
            Mean_Risk_Score=("Risk_Score", "mean"),
            Mean_Delay=("Delivery_Delay_Days", "mean"),
        ).reset_index()
    else:
        if "Mean_Delay" not in carrier_risk.columns and "Delivery_Delay_Days" in merged.columns:
            delay_agg = merged.groupby("Transport_Company")["Delivery_Delay_Days"].mean().reset_index()
            delay_agg.columns = ["Transport_Company", "Mean_Delay"]
            carrier_risk = carrier_risk.merge(delay_agg, on="Transport_Company", how="left")
        if "Shipment_Count" not in carrier_risk.columns:
            cnt = merged.groupby("Transport_Company")["Shipment_ID"].count().reset_index()
            cnt.columns = ["Transport_Company", "Shipment_Count"]
            carrier_risk = carrier_risk.merge(cnt, on="Transport_Company", how="left")

    _section_header("Carrier Leaderboard")
    display_df = carrier_risk.head(20)
    st.dataframe(display_df, use_container_width=True, height=280)

    _section_header("Top Risky Carriers")
    top_risky = carrier_risk.nlargest(10, "Mean_Risk_Score")
    fig1 = px.bar(top_risky, x="Transport_Company", y="Mean_Risk_Score", color="Mean_Risk_Score", color_continuous_scale="Reds", title="Top 10 Risky Carriers by Average Risk Score")
    fig1.update_layout(font=dict(family="Source Sans Pro"), margin=dict(b=120))
    st.plotly_chart(fig1, use_container_width=True)

    _section_header("Best Performing Carriers")
    best = carrier_risk.nsmallest(10, "Mean_Risk_Score")
    fig2 = px.bar(best, x="Transport_Company", y="Mean_Risk_Score", color="Mean_Risk_Score", color_continuous_scale="Greens", title="Top 10 Best Performing Carriers")
    fig2.update_layout(font=dict(family="Source Sans Pro"), margin=dict(b=120))
    st.plotly_chart(fig2, use_container_width=True)


def render_route_intelligence(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Route (Origin → Destination) analysis: most delayed, most risky, highest volume."""
    if merged.empty:
        st.info("No data to display.")
        return
    merged = merged.copy()
    merged["Route"] = merged["Origin"].astype(str) + " → " + merged["Destination"].astype(str)
    route_agg = merged.groupby("Route").agg(
        Shipments=("Shipment_ID", "count"),
        Avg_Delay=("Delivery_Delay_Days", "mean"),
        Avg_Risk=("Risk_Score", "mean"),
        Total_Exposure=("Invoice_Difference", "sum"),
    ).reset_index()

    _section_header("Most Delayed Routes")
    delayed = route_agg.nlargest(10, "Avg_Delay")
    fig1 = px.bar(delayed, x="Route", y="Avg_Delay", title="Top 10 Most Delayed Routes (Avg Days)", color="Avg_Delay", color_continuous_scale="Oranges")
    fig1.update_layout(xaxis_tickangle=-45, font=dict(family="Source Sans Pro"), margin=dict(b=150))
    st.plotly_chart(fig1, use_container_width=True)

    _section_header("Most Risky Routes")
    risky = route_agg.nlargest(10, "Avg_Risk")
    fig2 = px.bar(risky, x="Route", y="Avg_Risk", title="Top 10 Most Risky Routes", color="Avg_Risk", color_continuous_scale="Reds")
    fig2.update_layout(xaxis_tickangle=-45, font=dict(family="Source Sans Pro"), margin=dict(b=150))
    st.plotly_chart(fig2, use_container_width=True)

    _section_header("Highest Shipment Volume Routes")
    volume = route_agg.nlargest(10, "Shipments")
    fig3 = px.bar(volume, x="Route", y="Shipments", title="Top 10 Routes by Shipment Volume", color="Shipments", color_continuous_scale="Blues")
    fig3.update_layout(xaxis_tickangle=-45, font=dict(family="Source Sans Pro"), margin=dict(b=150))
    st.plotly_chart(fig3, use_container_width=True)


def render_financial_risk(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Cost leakage detector: invoice, weight, package mismatch and Potential Recoverable Amount."""
    if merged.empty:
        st.info("No data to display.")
        return
    invoice_leak = merged["Invoice_Difference"].sum()
    weight_leak = merged.get("Weight_Difference", pd.Series(0, index=merged.index)).fillna(0)
    if "Weight_KG" in merged.columns and weight_leak.abs().sum() > 0:
        weight_leak_amt = (weight_leak * 2).sum()  # placeholder per-unit cost
    else:
        weight_leak_amt = 0
    pkg_leak = merged.get("Quantity_Difference", pd.Series(0, index=merged.index)).fillna(0)
    pkg_leak_amt = (pkg_leak * 50).sum()  # placeholder per-package cost
    recoverable = invoice_leak + weight_leak_amt + pkg_leak_amt

    _section_header("Cost Leakage Detector")
    st.markdown(
        f'<div class="ln-metric-card"><span class="label">Potential Recoverable Amount</span><br><span class="value">₹{int(recoverable):,}</span></div>',
        unsafe_allow_html=True,
    )
    st.caption("Breakdown: Invoice mismatch + weight mismatch + package mismatch (estimated).")
    col1, col2, col3 = st.columns(3)
    col1.metric("Invoice Mismatch ₹", f"{int(invoice_leak):,}")
    col2.metric("Weight Mismatch (est.) ₹", f"{int(weight_leak_amt):,}")
    col3.metric("Package Mismatch (est.) ₹", f"{int(pkg_leak_amt):,}")

    if context and context.get("heatmap_data") is not None and not context["heatmap_data"].empty:
        _section_header("Financial Exposure by Lane")
        st.dataframe(context["heatmap_data"].head(20), use_container_width=True)


def render_fraud_pattern_analysis(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Drivers with highest risk, carriers with repeated mismatches, routes with frequent delays."""
    if merged.empty:
        st.info("No data to display.")
        return
    driver_risk = context.get("driver_risk") if context else insights_engine.driver_risk_score(merged)
    suspicious = insights_engine.suspicious_carrier_detection(merged) if hasattr(insights_engine, "suspicious_carrier_detection") else pd.DataFrame()
    merged = merged.copy()
    merged["Route"] = merged["Origin"].astype(str) + " → " + merged["Destination"].astype(str)
    route_delays = merged.groupby("Route")["Delivery_Delay_Days"].mean().nlargest(10).reset_index()

    _section_header("Drivers with Highest Risk Score")
    if driver_risk is not None and not driver_risk.empty:
        st.dataframe(driver_risk.head(15), use_container_width=True, height=300)
        fig = px.bar(driver_risk.head(10), x="Driver_Name", y="Mean_Risk_Score", color="Mean_Risk_Score", color_continuous_scale="Reds", title="Top 10 Highest Risk Drivers")
        st.plotly_chart(fig, use_container_width=True)
    else:
        drv = merged.groupby("Driver_Name")["Risk_Score"].mean().nlargest(10).reset_index()
        st.dataframe(drv, use_container_width=True)

    _section_header("Carriers with Repeated Mismatches")
    if not suspicious.empty:
        st.dataframe(suspicious, use_container_width=True)
    else:
        carr_mismatch = merged[merged["Invoice_Difference"] > 100].groupby("Transport_Company").size().nlargest(10).reset_index(name="Mismatch_Count")
        st.dataframe(carr_mismatch, use_container_width=True)

    _section_header("Routes with Frequent Delays")
    st.dataframe(route_delays, use_container_width=True)


def render_shipment_timeline(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Dispatch Date → Delivery Date with delayed shipments highlighted."""
    if merged.empty:
        st.info("No data to display.")
        return
    _section_header("Shipment Timeline")
    df = merged.copy()
    df["Dispatch_Date"] = pd.to_datetime(df["Dispatch_Date"], errors="coerce")
    df["Delivery_Date"] = pd.to_datetime(df["Delivery_Date"], errors="coerce")
    df = df.dropna(subset=["Dispatch_Date", "Delivery_Date"])
    if df.empty:
        st.warning("No valid dates in dataset.")
        return
    df["Delayed"] = df.get("Delivery_Delay_Days", 0) > 2
    fig = px.scatter(
        df,
        x="Dispatch_Date",
        y="Delivery_Date",
        color="Delayed",
        hover_name="Shipment_ID",
        color_discrete_map={True: "#c62828", False: "#51aa3a"},
        title="Dispatch Date → Delivery Date (Red = Delayed)",
    )
    fig.update_layout(font=dict(family="Source Sans Pro"))
    st.plotly_chart(fig, use_container_width=True)
    delayed_count = df["Delayed"].sum()
    st.metric("Delayed Shipments (delay > 2 days)", int(delayed_count))


def render_ai_copilot(merged: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> None:
    """Rule-based AI assistant: Which carriers cause delays? Most risky routes? Shipments needing investigation?"""
    if merged.empty:
        st.info("No data to display.")
        return
    _section_header("AI Logistics Copilot")
    st.caption("Ask a question (rule-based responses from your data).")
    q = st.text_input("Ask a question", placeholder="e.g. Which carriers are causing delays?")
    if q:
        q_lower = q.lower()
        if "carrier" in q_lower and ("delay" in q_lower or "delays" in q_lower):
            delay_agg = merged.groupby("Transport_Company")["Delivery_Delay_Days"].mean().sort_values(ascending=False).head(10)
            st.write("**Carriers with highest average delivery delay:**")
            st.dataframe(delay_agg.reset_index(), use_container_width=True)
        elif "route" in q_lower and ("risk" in q_lower or "risky" in q_lower):
            merged_copy = merged.copy()
            merged_copy["Route"] = merged_copy["Origin"].astype(str) + " → " + merged_copy["Destination"].astype(str)
            route_risk = merged_copy.groupby("Route")["Risk_Score"].mean().sort_values(ascending=False).head(10)
            st.write("**Most risky routes (by average risk score):**")
            st.dataframe(route_risk.reset_index(), use_container_width=True)
        elif "shipment" in q_lower and ("investigation" in q_lower or "investigate" in q_lower):
            need_inv = merged[merged["Risk_Level"].isin(["High", "Critical"])].head(20)
            st.write("**Shipments needing investigation (High/Critical risk):**")
            st.dataframe(need_inv[["Shipment_ID", "Risk_Level", "Risk_Score", "Recommended_Action"]].head(20), use_container_width=True)
        else:
            st.info("Try: 'Which carriers are causing delays?', 'Which routes are most risky?', or 'Which shipments need investigation?'")
    else:
        st.markdown("**Example questions:**")
        st.markdown("- Which carriers are causing delays?")
        st.markdown("- Which routes are most risky?")
        st.markdown("- Which shipments need investigation?")


