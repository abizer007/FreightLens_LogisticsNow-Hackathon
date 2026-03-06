# ==========================================================
# LogisticsNow Exception Intelligence Console
# AI-powered LR – POD – Invoice Reconciliation System
# ==========================================================

import hashlib
import logging
from io import BytesIO
from typing import Optional, Tuple

import streamlit as st

from modules import data_cleaning
from modules import data_loader
from modules import fraud_detection
from modules import insights_engine
from modules import reconciliation_engine
from modules import risk_engine
from modules import validators
from ui import dashboard
from ui import finance
from ui import fraud
from ui import operations
from ui import shipment_analysis
from ui import control_tower_views
from ui.brand_css import BRAND_CSS, BRAND_TAGLINE_HTML

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="LogisticsNow Intelligence Console",
    layout="wide",
)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<style>
.main-title { font-size:38px; font-weight:bold; color:#2E7D32; }
.sub-title { font-size:18px; color:gray; }
</style>
""", unsafe_allow_html=True)
st.markdown('<p class="main-title">LogisticsNow Exception Intelligence Console</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">AI Powered LR–POD–Invoice Reconciliation System</p>', unsafe_allow_html=True)
# Brand design system and tagline (LogisticsNow AI Console)
st.markdown(BRAND_CSS, unsafe_allow_html=True)
st.markdown(BRAND_TAGLINE_HTML, unsafe_allow_html=True)
st.divider()

# -----------------------------
# DATA UPLOAD
# -----------------------------
st.subheader("Upload Logistics Documents")
col1, col2, col3 = st.columns(3)
with col1:
    lr_file = st.file_uploader("Upload LR Dataset", type="csv")
with col2:
    pod_file = st.file_uploader("Upload POD Dataset", type="csv")
with col3:
    invoice_file = st.file_uploader("Upload Invoice Dataset", type="csv")


def _upload_hash(lr_file, pod_file, invoice_file) -> str:
    """Stable hash of uploads for cache key."""
    def read(f):
        if f is None:
            return b""
        f.seek(0)
        return f.read()
    h = hashlib.sha256()
    h.update(read(lr_file))
    h.update(read(pod_file))
    h.update(read(invoice_file))
    return h.hexdigest()


@st.cache_data(ttl=3600)
def _load_and_pipeline(cache_key: str, lr_bytes: bytes, pod_bytes: bytes, inv_bytes: bytes) -> Tuple[Optional[object], Optional[object], Optional[object]]:
    """Load CSVs and run full pipeline; returns (merged_clean, fraud_flags, context_dict)."""
    import pandas as pd
    from io import BytesIO
    if not lr_bytes or not pod_bytes or not inv_bytes:
        return None, None, None
    lr_df = pd.read_csv(BytesIO(lr_bytes))
    pod_df = pd.read_csv(BytesIO(pod_bytes))
    inv_df = pd.read_csv(BytesIO(inv_bytes))
    merged = reconciliation_engine.merge_documents(lr_df, pod_df, inv_df)
    merged = reconciliation_engine.detect_discrepancies(merged)
    merged = validators.validate_and_normalize_merged(merged)
    merged = data_cleaning.clean_dataset(merged)
    merged = data_cleaning.strip_validation_columns(merged)
    merged = risk_engine.run_risk_pipeline(merged)
    fraud_flags = fraud_detection.run_fraud_detection(merged)
    context = {
        "carrier_risk": insights_engine.carrier_risk_score(merged),
        "driver_risk": insights_engine.driver_risk_score(merged),
        "lane_risk": insights_engine.lane_risk_score(merged),
        "delay_trends": insights_engine.shipment_delay_trends(merged),
        "heatmap_data": insights_engine.financial_exposure_heatmap_data(merged),
        "insights_summary": insights_engine.auto_investigation_summary(merged),
    }
    return merged, fraud_flags, context


# -----------------------------
# PROCESS AND NAVIGATION
# -----------------------------
if lr_file and pod_file and invoice_file:
    cache_key = _upload_hash(lr_file, pod_file, invoice_file)
    lr_file.seek(0)
    pod_file.seek(0)
    invoice_file.seek(0)
    lr_bytes = lr_file.read()
    pod_bytes = pod_file.read()
    inv_bytes = invoice_file.read()
    merged, fraud_flags, context = _load_and_pipeline(cache_key, lr_bytes, pod_bytes, inv_bytes)

    if merged is None or merged.empty:
        st.warning("Pipeline produced no data. Check file formats.")
    else:
        # Top navigation (Logistics Control Tower) - session state
        if "show_top_nav_content" not in st.session_state:
            st.session_state.show_top_nav_content = True
        if "top_nav_page" not in st.session_state:
            st.session_state.top_nav_page = "Control Tower"
        if "prev_sidebar_page" not in st.session_state:
            st.session_state.prev_sidebar_page = None

        TOP_NAV_PAGES = [
            "Control Tower",
            "Shipment Intelligence",
            "Carrier Analytics",
            "Route Intelligence",
            "Financial Risk",
            "Fraud Detection",
            "AI Logistics Copilot",
        ]
        # Sidebar: Reports on top, then Control Tower buttons
        st.sidebar.markdown("**LogisticsNow Intelligence Console**")
        st.sidebar.markdown("---")
        st.sidebar.markdown('<p class="ln-sidebar-heading">Reports</p>', unsafe_allow_html=True)
        page = st.sidebar.selectbox(
            "View",
            [
                "Executive Dashboard",
                "Shipment Risk Analysis",
                "Operational Intelligence",
                "Financial Intelligence",
                "Fraud & Compliance",
            ],
            key="sidebar_reports",
        )
        st.sidebar.markdown("---")
        st.sidebar.markdown('<p class="ln-sidebar-heading ln-sidebar-spaced">Logistics Control Tower</p>', unsafe_allow_html=True)
        for i, name in enumerate(TOP_NAV_PAGES):
            if st.sidebar.button(name, key=f"top_nav_{i}"):
                st.session_state.show_top_nav_content = True
                st.session_state.top_nav_page = name
                st.rerun()
        if page != st.session_state.prev_sidebar_page:
            st.session_state.show_top_nav_content = False
            st.session_state.prev_sidebar_page = page

        if st.session_state.show_top_nav_content:
            p = st.session_state.top_nav_page
            if p == "Control Tower":
                control_tower_views.render_control_tower(merged, context)
            elif p == "Shipment Intelligence":
                control_tower_views.render_shipment_intelligence(merged, context)
            elif p == "Carrier Analytics":
                control_tower_views.render_carrier_analytics(merged, context)
            elif p == "Route Intelligence":
                control_tower_views.render_route_intelligence(merged, context)
            elif p == "Financial Risk":
                control_tower_views.render_financial_risk(merged, context)
            elif p == "Fraud Detection":
                control_tower_views.render_fraud_pattern_analysis(merged, context)
            elif p == "AI Logistics Copilot":
                control_tower_views.render_ai_copilot(merged, context)
        elif page == "Executive Dashboard":
            dashboard.render(
                merged,
                insights_summary=context.get("insights_summary"),
                carrier_risk=context.get("carrier_risk"),
                delay_trends=context.get("delay_trends"),
            )
        elif page == "Shipment Risk Analysis":
            shipment_analysis.render(merged)
        elif page == "Operational Intelligence":
            operations.render(
                merged,
                carrier_risk=context.get("carrier_risk"),
                driver_risk=context.get("driver_risk"),
                lane_risk=context.get("lane_risk"),
                delay_trends=context.get("delay_trends"),
            )
        elif page == "Financial Intelligence":
            finance.render(merged, heatmap_data=context.get("heatmap_data"))
        elif page == "Fraud & Compliance":
            fraud.render(merged, fraud_flags=fraud_flags)
else:
    st.info("Upload LR, POD and Invoice datasets to begin reconciliation.")
