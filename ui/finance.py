"""
Financial Intelligence: exposure, heatmap, charge breakdown.
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import streamlit as st

from modules import insights_engine


def render(
    merged: pd.DataFrame,
    heatmap_data: Optional[pd.DataFrame] = None,
) -> None:
    """Render Financial Intelligence page."""
    if merged.empty:
        st.info("No data to display.")
        return

    discrepancy_value = merged["Invoice_Difference"].sum()
    st.subheader("Financial Exposure")
    st.metric("Total Invoice Discrepancy ₹", f"{int(discrepancy_value):,}")

    st.subheader("Freight Cost Composition")
    charge_cols = ["Freight_Charge", "Fuel_Surcharge", "Tax"]
    available = [c for c in charge_cols if c in merged.columns]
    if available:
        charges = merged[available].sum()
        charges_df = charges.reset_index()
        charges_df.columns = ["Charge Type", "Amount"]
        fig = px.pie(
            charges_df,
            names="Charge Type",
            values="Amount",
            title="Charge breakdown",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.write("Charge columns not available.")

    st.subheader("Financial Exposure Heatmap")
    if heatmap_data is None or (isinstance(heatmap_data, pd.DataFrame) and heatmap_data.empty):
        heatmap_data = insights_engine.financial_exposure_heatmap_data(merged)
    if heatmap_data is not None and not heatmap_data.empty:
        pivot = heatmap_data.pivot_table(
            index="Transport_Company",
            columns="Lane",
            values="Invoice_Difference",
            aggfunc="sum",
            fill_value=0,
        )
        if not pivot.empty:
            fig_heat = px.imshow(
                pivot,
                labels=dict(x="Lane", y="Carrier", color="Exposure ₹"),
                title="Financial exposure by carrier and lane",
                aspect="auto",
            )
            st.plotly_chart(fig_heat, use_container_width=True)
        else:
            st.dataframe(heatmap_data, use_container_width=True)
    else:
        st.write("No heatmap data.")
