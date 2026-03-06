# Brand design system for LogisticsNow AI Console
# Fonts: Poppins (headings), Source Sans Pro (body)
# Primary Green: #51aa3a, White: #ffffff, Dark: #21242b, Light BG: #f2f4f8

BRAND_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&family=Source+Sans+Pro:wght@400;600&display=swap');
:root {
  --ln-primary: #51aa3a;
  --ln-white: #ffffff;
  --ln-dark: #21242b;
  --ln-light: #f2f4f8;
  --ln-risk-high: #c62828;
  --ln-risk-medium: #ef6c00;
  --ln-risk-low: #2e7d32;
}
.ln-tagline { font-family: 'Source Sans Pro', sans-serif; font-size: 14px; color: #51aa3a; margin-top: 4px; letter-spacing: 0.5px; }
.ln-section-title { font-family: 'Poppins', sans-serif; font-weight: 700; font-size: 22px; color: #21242b; margin-bottom: 16px; }
.ln-metric-card {
  font-family: 'Poppins', sans-serif;
  background: linear-gradient(135deg, rgba(255,255,255,0.95) 0%, rgba(242,244,248,0.9) 100%);
  backdrop-filter: blur(8px); border-radius: 12px; padding: 20px; margin: 8px 0;
  border-left: 4px solid #51aa3a; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  transition: box-shadow 0.2s ease;
}
.ln-metric-card:hover { box-shadow: 0 4px 16px rgba(81,170,58,0.15); }
.ln-metric-card .value { font-size: 28px; font-weight: 700; color: #21242b; }
.ln-metric-card .label { font-family: 'Source Sans Pro', sans-serif; font-size: 13px; color: #666; }
.stPlotlyChart { margin-bottom: 24px; }

/* Top navigation buttons: fluid, responsive, branded */
.stButton { display: inline-block; margin-right: 6px; margin-bottom: 6px; }
.stButton > button {
  font-family: 'Poppins', sans-serif;
  background: #21242b;
  color: #f2f4f8;
  border-radius: 999px;
  border: 1px solid #51aa3a;
  padding: 6px 14px;
  font-size: 13px;
  white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
}
.stButton > button:hover {
  background: #51aa3a;
  color: #ffffff;
  box-shadow: 0 0 0 1px rgba(81,170,58,0.4);
}

/* Sidebar: section headings (Reports, Control Tower Views) - same font, bigger, green */
[data-testid="stSidebar"] .ln-sidebar-heading {
  font-family: 'Poppins', sans-serif;
  font-weight: 700;
  font-size: 17px;
  color: #51aa3a;
  letter-spacing: 0.3px;
  margin-bottom: 0;
}
[data-testid="stSidebar"] .ln-sidebar-spaced {
  margin-bottom: 14px;
}
[data-testid="stSidebar"] .stButton {
  display: block;
  margin-bottom: 6px;
  width: 100%;
}
[data-testid="stSidebar"] .stButton > button {
  width: 100%;
  font-family: 'Poppins', sans-serif;
  font-size: 13px;
  background: #21242b;
  color: #f2f4f8;
  border: 1px solid #51aa3a;
  border-radius: 8px;
  padding: 8px 14px;
  white-space: nowrap;
  transition: background 0.15s ease, color 0.15s ease;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background: #51aa3a;
  color: #ffffff;
}

.ln-alert-warning { border-left: 4px solid #ef6c00; }
.ln-alert-error { border-left: 4px solid #c62828; }
.ln-alert-success { border-left: 4px solid #51aa3a; }
.ln-footer { font-family: 'Source Sans Pro', sans-serif; font-size: 12px; color: #666; margin-top: 32px; padding: 16px; }
.ln-values { color: #51aa3a; font-weight: 600; }
</style>
"""

BRAND_TAGLINE_HTML = """
<p class="ln-tagline">Building the Digital Backbone of Logistics</p>
"""

BRAND_VALUES_HTML = """
<p class="ln-footer">LogisticsNow values: <span class="ln-values">Trust</span> · <span class="ln-values">Neutrality</span> · <span class="ln-values">Efficiency</span> · <span class="ln-values">Visibility</span> · <span class="ln-values">Innovation</span></p>
"""
