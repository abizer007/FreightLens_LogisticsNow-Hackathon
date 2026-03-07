# FreightLens Control Tower – sidebar component
# Modern SaaS-style sidebar with nav items, session_state, and injected CSS.

import sys
import base64
from pathlib import Path

import streamlit as st

# Ensure local component modules resolve even when app is launched from another cwd.
_COMPONENTS_DIR = Path(__file__).resolve().parent
if str(_COMPONENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_COMPONENTS_DIR))

try:
    from components.navigation import (
        CONTROL_TOWER_NAV,
        KEY_NAV_PAGE,
        KEY_SHOW_TOP_NAV,
        KEY_PREV_REPORTS_PAGE,
        NAV_ID_TO_PAGE_NAME,
        NavItem,
    )
except ModuleNotFoundError:
    from navigation import (  # type: ignore
        CONTROL_TOWER_NAV,
        KEY_NAV_PAGE,
        KEY_SHOW_TOP_NAV,
        KEY_PREV_REPORTS_PAGE,
        NAV_ID_TO_PAGE_NAME,
        NavItem,
    )


def _load_sidebar_css() -> str:
    """Load sidebar CSS from styles/sidebar.css or return embedded default."""
    css_path = Path(__file__).resolve().parent.parent / "styles" / "sidebar.css"
    if css_path.exists():
        return css_path.read_text(encoding="utf-8")
    return ""


def _inject_sidebar_styles():
    """Inject custom CSS for sidebar (container, buttons, hover, active)."""
    css = _load_sidebar_css()
    if not css.strip():
        return
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


def _nav_button_key(item: NavItem) -> str:
    return f"nav_{item.id}"


def _init_sidebar_state() -> None:
    """Initialize sidebar session-state defaults used for routing."""
    if KEY_NAV_PAGE not in st.session_state:
        st.session_state[KEY_NAV_PAGE] = "Overview"
    if KEY_SHOW_TOP_NAV not in st.session_state:
        st.session_state[KEY_SHOW_TOP_NAV] = True
    if KEY_PREV_REPORTS_PAGE not in st.session_state:
        st.session_state[KEY_PREV_REPORTS_PAGE] = None


def _select_control_tower_page(page_name: str) -> None:
    """Set selected control tower page and switch content mode."""
    st.session_state[KEY_NAV_PAGE] = page_name
    st.session_state[KEY_SHOW_TOP_NAV] = True


def _resolve_sidebar_logo_path() -> Path | None:
    """Resolve logo path for sidebar title replacement."""
    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / "freightlens-logo.png",
        project_root / "assets" / "full_logo.png",
        project_root / "assets" / "logo.png",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def _render_static_sidebar_logo(logo_path: Path) -> None:
    """Render a non-interactive static logo using inline HTML."""
    img_bytes = logo_path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("ascii")
    st.sidebar.markdown(
        (
            '<div class="fl-sidebar-logo-static-wrap">'
            f'<img class="fl-sidebar-logo-static" src="data:image/png;base64,{b64}" alt="FreightLens logo" />'
            "</div>"
        ),
        unsafe_allow_html=True,
    )


def render_sidebar(
    *,
    reports_options: list[str],
    reports_key: str = "sidebar_reports",
) -> tuple[str | None, str | None]:
    """
    Render the FreightLens Control Tower sidebar:
    - Title at top
    - Control Tower nav items (icon + text, card-style buttons)
    - Reports selectbox below (optional)

    Uses session_state for active nav page and report selection.
    Returns (selected_report_page, selected_nav_page_name) for app routing.
    """
    _inject_sidebar_styles()

    # Session state defaults
    _init_sidebar_state()

    # ---- Title / Logo (compact) ----
    logo_path = _resolve_sidebar_logo_path()
    if logo_path is not None:
        _render_static_sidebar_logo(logo_path)
    else:
        st.sidebar.markdown(
            '<p class="fl-sidebar-title">FreightLens Control Tower</p>',
            unsafe_allow_html=True,
        )
    st.sidebar.markdown('<div class="fl-sidebar-spacer"></div>', unsafe_allow_html=True)

    # ---- Reports (dropdown above navigation) ----
    st.sidebar.markdown(
        '<p class="fl-sidebar-section-label">Reports</p>',
        unsafe_allow_html=True,
    )
    page = st.sidebar.selectbox(
        "View",
        reports_options,
        key=reports_key,
        label_visibility="collapsed",
    )
    if page != st.session_state.get(KEY_PREV_REPORTS_PAGE):
        st.session_state[KEY_SHOW_TOP_NAV] = False
        st.session_state[KEY_PREV_REPORTS_PAGE] = page

    st.sidebar.markdown('<div class="fl-sidebar-spacer"></div>', unsafe_allow_html=True)

    # ---- Control Tower navigation ----
    st.sidebar.markdown(
        '<p class="fl-sidebar-section-label">Navigation</p>',
        unsafe_allow_html=True,
    )
    current_page = st.session_state.get(KEY_NAV_PAGE, "Overview")

    for item in CONTROL_TOWER_NAV:
        page_name = NAV_ID_TO_PAGE_NAME[item.id]
        is_active = current_page == page_name
        if is_active:
            st.sidebar.markdown(
                f'<div class="fl-nav-item fl-nav-item-active">'
                f'<span class="fl-nav-icon">{item.icon}</span>'
                f'<span class="fl-nav-label">{item.label}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
        else:
            btn_key = _nav_button_key(item)
            if st.sidebar.button(
                f"  {item.icon}  {item.label}",
                key=btn_key,
                width="stretch",
            ):
                _select_control_tower_page(page_name)
                st.rerun()

    return page, st.session_state[KEY_NAV_PAGE]


def get_show_control_tower_content() -> bool:
    """Whether to show Control Tower content (vs Reports content)."""
    return st.session_state.get(KEY_SHOW_TOP_NAV, True)
