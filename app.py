# ==========================================================
# LogisticsNow AI Reconciliation Console
# LR – POD – Invoice Matching Agent
# Hackathon Prototype
# ==========================================================

# -----------------------------
# IMPORTS
# -----------------------------

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    page_title="LogisticsNow AI Reconciliation",
    layout="wide"
)

# -----------------------------
# HEADER STYLE
# -----------------------------

st.markdown("""
<style>
.main-title {
    font-size:38px;
    font-weight:bold;
    color:#2E7D32;
}
.sub-title {
    font-size:18px;
    color:gray;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">LogisticsNow Exception Intelligence Console</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">AI Powered LR–POD–Invoice Reconciliation System</p>', unsafe_allow_html=True)

st.divider()

# ==========================================================
# DATA UPLOAD
# ==========================================================

st.subheader("Upload Logistics Documents")

col1, col2, col3 = st.columns(3)

with col1:
    lr_file = st.file_uploader("Upload LR Dataset", type="csv")

with col2:
    pod_file = st.file_uploader("Upload POD Dataset", type="csv")

with col3:
    invoice_file = st.file_uploader("Upload Invoice Dataset", type="csv")

# ==========================================================
# PROCESS DATA
# ==========================================================

if lr_file and pod_file and invoice_file:

    lr_df = pd.read_csv(lr_file)
    pod_df = pd.read_csv(pod_file)
    inv_df = pd.read_csv(invoice_file)

    merged = lr_df.merge(pod_df, on="Shipment_ID", how="left")
    merged = merged.merge(inv_df, on="Shipment_ID", how="left")

    # ======================================================
    # DISCREPANCY DETECTION
    # ======================================================

    merged["Quantity_Difference"] = abs(
        merged["Package_Count"] - merged["Received_Packages"]
    )

    merged["Expected_Amount"] = (
        merged["Freight"] +
        merged["Loading_Charges"] +
        merged["Unloading_Charges"]
    )

    merged["Invoice_Difference"] = abs(
        merged["Expected_Amount"] - merged["Total_Invoice_Amount"]
    )

    merged["Weight_Difference"] = abs(
        merged["Weight_KG"] - merged["Charged_Weight"]
    )

    merged["Dispatch_Date"] = pd.to_datetime(merged["Dispatch_Date"])
    merged["Delivery_Date"] = pd.to_datetime(merged["Delivery_Date"])

    merged["Delivery_Delay_Days"] = (
        merged["Delivery_Date"] - merged["Dispatch_Date"]
    ).dt.days

    merged["Missing_Signature"] = merged["Signature_Available"] == "No"
    merged["POD_Missing"] = merged["Status"] != "Delivered"

    # ======================================================
    # RISK SCORE
    # ======================================================

    merged["Risk_Score"] = (
        merged["Quantity_Difference"] * 3 +
        merged["Invoice_Difference"] * 0.1 +
        merged["Delivery_Delay_Days"] * 5 +
        merged["Weight_Difference"] * 0.05 +
        merged["Missing_Signature"] * 10 +
        merged["POD_Missing"] * 20
    )

    merged["Risk_Level"] = np.where(
        merged["Risk_Score"] > 60, "High",
        np.where(merged["Risk_Score"] > 25, "Medium", "Low")
    )

    # ======================================================
    # ACTION RECOMMENDATION AGENT
    # ======================================================

    def recommend_action(row):

        if row["POD_Missing"]:
            return "Request POD confirmation"

        elif row["Quantity_Difference"] > 0:
            return "Verify package count"

        elif row["Invoice_Difference"] > 100:
            return "Investigate invoice mismatch"

        elif row["Delivery_Delay_Days"] > 2:
            return "Review carrier performance"

        else:
            return "Auto approve payment"

    merged["Recommended_Action"] = merged.apply(recommend_action, axis=1)

    # ======================================================
    # AI EXPLANATION GENERATOR
    # ======================================================

    def generate_explanation(row):

        return f"""
Shipment {row['Shipment_ID']} has a **{row['Risk_Level']} risk profile**.

Observations:
• Quantity difference: {row['Quantity_Difference']}
• Invoice discrepancy: ₹{int(row['Invoice_Difference'])}
• Delivery delay: {row['Delivery_Delay_Days']} days
• Weight mismatch: {round(row['Weight_Difference'],2)} kg

Recommended Action:
{row['Recommended_Action']}
"""

    merged["AI_Explanation"] = merged.apply(generate_explanation, axis=1)

    # ======================================================
    # GLOBAL METRICS
    # ======================================================

    total_shipments = len(merged)
    high_risk = len(merged[merged["Risk_Level"] == "High"])
    medium_risk = len(merged[merged["Risk_Level"] == "Medium"])
    discrepancy_value = merged["Invoice_Difference"].sum()

    # ======================================================
    # SIDEBAR NAVIGATION
    # ======================================================

    st.sidebar.title("LogisticsNow AI Console")

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard Overview",
            "Shipment Risk Analysis",
            "Operational Intelligence",
            "Financial Intelligence",
            "Fraud Detection"
        ]
    )

    # ======================================================
    # PAGE 1 — DASHBOARD OVERVIEW
    # ======================================================

    if page == "Dashboard Overview":

        st.subheader("Operational Overview")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Shipments", total_shipments)
        col2.metric("High Risk Shipments", high_risk)
        col3.metric("Medium Risk Shipments", medium_risk)
        col4.metric("Financial Risk ₹", int(discrepancy_value))

        st.divider()

        st.subheader("Risk Distribution")

        fig = px.pie(
            merged,
            names="Risk_Level",
            title="Shipment Risk Breakdown",
            color="Risk_Level",
            color_discrete_map={
                "High":"red",
                "Medium":"orange",
                "Low":"green"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

        st.subheader("AI Generated Operational Insights")

        insights = []

        if high_risk > 40:
            insights.append("Large number of high risk shipments detected.")

        if merged["Delivery_Delay_Days"].mean() > 2:
            insights.append("Delivery delays exceed expected service levels.")

        if discrepancy_value > 100000:
            insights.append("High financial discrepancy detected across invoices.")

        for i in insights:
            st.info(i)

    # ======================================================
    # PAGE 2 — SHIPMENT RISK ANALYSIS
    # ======================================================

    if page == "Shipment Risk Analysis":

        st.subheader("Shipment Risk Overview")

        risk_filter = st.selectbox(
            "Filter by Risk Level",
            ["All","High","Medium","Low"]
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
            "Recommended_Action"
        ]

        st.dataframe(
            risk_table[display_cols],
            use_container_width=True,
            height=350
        )

        st.divider()

        st.subheader("Shipment Investigation")

        selected = st.selectbox(
            "Select Shipment",
            merged["Shipment_ID"]
        )

        shipment = merged[merged["Shipment_ID"] == selected].iloc[0]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown("### Shipment Details")
            st.write("Origin:", shipment["Origin"])
            st.write("Destination:", shipment["Destination"])
            st.write("Material:", shipment["Material"])

        with col2:
            st.markdown("### Transport Info")
            st.write("Carrier:", shipment["Transport_Company"])
            st.write("Driver:", shipment["Driver_Name"])
            st.write("Vehicle:", shipment["Vehicle_Number"])

        with col3:
            st.markdown("### Risk Metrics")
            st.write("Risk Level:", shipment["Risk_Level"])
            st.write("Risk Score:", round(shipment["Risk_Score"],2))
            st.write("Delivery Delay:", shipment["Delivery_Delay_Days"])

        st.markdown("### AI Investigation Summary")
        st.info(shipment["AI_Explanation"])

    # ======================================================
    # PAGE 3 — OPERATIONAL INTELLIGENCE
    # ======================================================

    if page == "Operational Intelligence":

        st.subheader("Carrier Performance")

        carrier_perf = merged.groupby("Transport_Company").agg({

            "Shipment_ID":"count",
            "Delivery_Delay_Days":"mean",
            "Risk_Score":"mean"

        }).reset_index()

        fig = px.bar(
            carrier_perf,
            x="Transport_Company",
            y="Risk_Score",
            color="Risk_Score"
        )

        st.plotly_chart(fig)

        st.subheader("Driver Performance")

        driver_perf = merged.groupby("Driver_Name").agg({

            "Shipment_ID":"count",
            "Delivery_Delay_Days":"mean",
            "Risk_Score":"mean"

        }).reset_index()

        st.dataframe(driver_perf.sort_values("Risk_Score",ascending=False))

    # ======================================================
    # PAGE 4 — FINANCIAL INTELLIGENCE
    # ======================================================

    if page == "Financial Intelligence":

        st.subheader("Freight Cost Composition")

        charges = merged[[
            "Freight_Charge",
            "Fuel_Surcharge",
            "Tax"
        ]].sum()

        charges_df = charges.reset_index()
        charges_df.columns = ["Charge Type","Amount"]

        fig = px.pie(
            charges_df,
            names="Charge Type",
            values="Amount"
        )

        st.plotly_chart(fig)

        st.subheader("Financial Exposure")

        st.metric(
            "Total Invoice Discrepancy ₹",
            int(discrepancy_value)
        )

    # ======================================================
    # PAGE 5 — FRAUD DETECTION
    # ======================================================

    if page == "Fraud Detection":

        st.subheader("Duplicate Invoices")

        duplicates = merged[merged.duplicated("Invoice_ID", keep=False)]

        st.dataframe(duplicates)

        st.subheader("Missing POD or Signature")

        pod_risk = merged[
            (merged["Missing_Signature"]) |
            (merged["POD_Missing"])
        ]

        st.dataframe(pod_risk)

else:

    st.info("Upload LR, POD and Invoice datasets to begin reconciliation.")