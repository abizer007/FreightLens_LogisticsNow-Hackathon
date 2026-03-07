# ==========================================================
# FreightLens Exception Intelligence Console
# AI-powered LR – POD – Invoice Reconciliation System
# ==========================================================

import sys
from pathlib import Path

# Ensure project root is on path so 'components', 'modules', 'ui' resolve
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

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
from ui import report_panel
from ui.brand_css import BRAND_CSS, BRAND_TAGLINE_HTML
try:
    from components.sidebar import get_show_control_tower_content, render_sidebar
except ModuleNotFoundError:
    # Fallback: load sidebar directly from file path.
    import importlib.util

    _sidebar_path = _ROOT / "components" / "sidebar.py"
    _spec = importlib.util.spec_from_file_location("sidebar_fallback", _sidebar_path)
    if _spec is None or _spec.loader is None:
        raise
    _module = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_module)
    get_show_control_tower_content = _module.get_show_control_tower_content
    render_sidebar = _module.render_sidebar

# -----------------------------
# PAGE CONFIG (must be first Streamlit command)
# -----------------------------
_favicon_path = _ROOT / "WhatsApp Image 2026-03-07 at 8.20.05 PM.jpeg"
_page_icon = str(_favicon_path) if _favicon_path.exists() else "📊"
st.set_page_config(
    page_title="FreightLens Dashboard",
    page_icon=_page_icon,
    layout="wide",
)

# Inject sidebar styles early so sidebar theme applies before data is loaded
_sidebar_css_path = Path(__file__).resolve().parent / "styles" / "sidebar.css"
if _sidebar_css_path.exists():
    st.markdown(
        f"<style>\n{_sidebar_css_path.read_text(encoding='utf-8')}\n</style>",
        unsafe_allow_html=True,
    )

# -----------------------------
# LOGGING
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# -----------------------------
# HEADER
# -----------------------------
st.markdown("""
<style>
.main-title { font-size:38px; font-weight:bold; color:#2E7D32; }
.sub-title { font-size:18px; color:#1F2937; }
</style>
""", unsafe_allow_html=True)
st.markdown('<p class="main-title">FreightLens Intelligence Console</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">AI Powered LR–POD–Invoice Reconciliation System</p>', unsafe_allow_html=True)
# Brand design system and tagline (FreightLens)
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
# SIDEBAR (always render for consistent modern SaaS look)
# -----------------------------
REPORTS_OPTIONS = [
    "Executive Dashboard",
    "Shipment Risk Analysis",
    "Operational Intelligence",
    "Financial Intelligence",
    "Fraud & Compliance",
]
page, nav_page = render_sidebar(reports_options=REPORTS_OPTIONS)
show_control_tower = get_show_control_tower_content()

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
        if show_control_tower:
            p = nav_page
            if p == "Overview":
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
            elif p == "Generate Intelligence Report":
                report_panel.render_report_panel(merged, context, fraud_flags)
        else:
            if page == "Executive Dashboard":
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
