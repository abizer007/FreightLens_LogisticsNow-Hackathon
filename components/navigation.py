# FreightLens Control Tower – navigation configuration
# Defines sidebar nav items with id, label, and icon for a modern SaaS-style sidebar.

from typing import List, NamedTuple


class NavItem(NamedTuple):
    """Single navigation item: id (for session_state), label, icon (emoji)."""
    id: str
    label: str
    icon: str


# Control Tower main navigation (Notion/Stripe/Linear-style)
CONTROL_TOWER_NAV: List[NavItem] = [
    NavItem("overview", "Overview", "📊"),
    NavItem("shipment_intelligence", "Shipment Intelligence", "🚚"),
    NavItem("carrier_analytics", "Carrier Analytics", "🏢"),
    NavItem("route_intelligence", "Route Intelligence", "🛣️"),
    NavItem("financial_risk", "Financial Risk", "💰"),
    NavItem("fraud_detection", "Fraud Detection", "🔍"),
    NavItem("ai_copilot", "Freggie Assist", "🤖"),
    NavItem("generate_intelligence_report", "Generate Intelligence Report", "📄"),
]

# Map nav id -> display name used in app routing
NAV_ID_TO_PAGE_NAME = {
    "overview": "Overview",
    "shipment_intelligence": "Shipment Intelligence",
    "carrier_analytics": "Carrier Analytics",
    "route_intelligence": "Route Intelligence",
    "financial_risk": "Financial Risk",
    "fraud_detection": "Fraud Detection",
    "ai_copilot": "Freggie Assist",
    "generate_intelligence_report": "Generate Intelligence Report",
}

# Session state keys
KEY_NAV_PAGE = "top_nav_page"
KEY_SHOW_TOP_NAV = "show_top_nav_content"
KEY_PREV_REPORTS_PAGE = "prev_sidebar_page"
