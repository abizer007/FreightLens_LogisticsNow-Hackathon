"""FreightLens enterprise intelligence report generator."""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional

import matplotlib
import numpy as np
import pandas as pd
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen.canvas import Canvas


matplotlib.use("Agg")
import matplotlib.pyplot as plt


ProgressCallback = Optional[Callable[[float, str], None]]
MAX_HIST_POINTS = 50000
SECTION_SPACER = 0.14 * inch
CHART_SPACER = 0.20 * inch


def _emit_progress(callback: ProgressCallback, value: float, message: str) -> None:
    if callback is not None:
        callback(float(max(0.0, min(1.0, value))), message)


def _to_df(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value.copy()
    return pd.DataFrame()


def _safe_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _downsample_series(series: pd.Series, max_points: int = MAX_HIST_POINTS) -> pd.Series:
    """Keep histograms responsive for very large datasets."""
    if len(series) <= max_points:
        return series
    return series.sample(max_points, random_state=42)


def _figure_to_rl_image(fig: plt.Figure, width_in: float = 6.8, height_in: float = 3.6) -> RLImage:
    buffer = BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buffer.seek(0)
    chart = RLImage(buffer, width=width_in * inch, height=height_in * inch)
    chart.hAlign = "CENTER"
    return chart


def _table_from_df(
    df: pd.DataFrame,
    max_rows: int = 15,
    round_cols: Optional[Iterable[str]] = None,
) -> Table:
    if df.empty:
        data = [["No data available"]]
        table = Table(data, hAlign="LEFT")
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2937")),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        return table

    work = df.head(max_rows).copy()
    if round_cols:
        for col in round_cols:
            if col in work.columns:
                work[col] = pd.to_numeric(work[col], errors="coerce").round(2)
    numeric_col_idx = [
        idx
        for idx, col in enumerate(work.columns)
        if pd.api.types.is_numeric_dtype(work[col])
    ]
    work = work.fillna("")
    headers = [str(c) for c in work.columns]
    rows = work.astype(str).values.tolist()
    data = [headers] + rows
    table = Table(data, hAlign="LEFT", repeatRows=1)
    style_rules = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E7D32")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#1F2937")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D0D7DE")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    for row_idx in range(1, len(data)):
        row_bg = colors.HexColor("#FFFFFF") if row_idx % 2 == 0 else colors.HexColor("#F3F6F4")
        style_rules.append(("BACKGROUND", (0, row_idx), (-1, row_idx), row_bg))
    for col_idx in numeric_col_idx:
        style_rules.append(("ALIGN", (col_idx, 1), (col_idx, -1), "RIGHT"))
    table.setStyle(TableStyle(style_rules))
    return table


def _styles() -> Dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=sample["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            textColor=colors.HexColor("#1F2937"),
            alignment=1,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "SubTitle",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=14,
            textColor=colors.HexColor("#6B7280"),
            alignment=1,
            spaceAfter=6,
        ),
        "meta": ParagraphStyle(
            "Meta",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#9CA3AF"),
            alignment=1,
            spaceAfter=10,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=sample["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=colors.HexColor("#2E7D32"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=sample["Normal"],
            fontName="Helvetica",
            fontSize=10,
            textColor=colors.HexColor("#111827"),
            leading=14,
            spaceAfter=6,
        ),
        "kpi": ParagraphStyle(
            "Kpi",
            parent=sample["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=colors.HexColor("#111827"),
            leading=14,
            spaceAfter=4,
        ),
    }


def _insights_as_text(insights_summary: Any, max_items: int = 6) -> List[str]:
    lines: List[str] = []
    if isinstance(insights_summary, list):
        for item in insights_summary[:max_items]:
            if isinstance(item, dict):
                msg = item.get("message")
                if isinstance(msg, str) and msg.strip():
                    lines.append(msg.strip())
            elif isinstance(item, str) and item.strip():
                lines.append(item.strip())
    elif isinstance(insights_summary, str) and insights_summary.strip():
        lines.append(insights_summary.strip())
    return lines


class _NumberedCanvas(Canvas):
    """Canvas with centered footer and page X of Y."""

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []

    def showPage(self) -> None:
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_footer(page_count)
            super().showPage()
        super().save()

    def _draw_footer(self, page_count: int) -> None:
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6B7280"))
        footer = (
            f"FreightLens Intelligence Platform   |   Generated by FreightLens AI   |   "
            f"Page {self._pageNumber} of {page_count}"
        )
        self.drawCentredString(A4[0] / 2.0, 18, footer)
        self.restoreState()


def _compute_kpis(merged: pd.DataFrame, fraud_flags: pd.DataFrame) -> Dict[str, float]:
    total_shipments = float(len(merged))
    discrepancies = 0.0
    if "Invoice_Difference" in merged.columns:
        discrepancies += float((_safe_numeric(merged["Invoice_Difference"]).abs() > 0).sum())
    if "Quantity_Difference" in merged.columns:
        discrepancies += float((_safe_numeric(merged["Quantity_Difference"]).abs() > 0).sum())
    discrepancies = min(discrepancies, total_shipments) if total_shipments else 0.0

    high_risk = 0.0
    if "Risk_Level" in merged.columns:
        high_risk = float(merged["Risk_Level"].isin(["High", "Critical"]).sum())
    elif "Risk_Score" in merged.columns:
        high_risk = float((_safe_numeric(merged["Risk_Score"]) >= 60).sum())

    delayed = 0.0
    if "Delivery_Delay_Days" in merged.columns:
        delayed = float((_safe_numeric(merged["Delivery_Delay_Days"]) > 0).sum())

    fraud_cases = float(len(fraud_flags)) if isinstance(fraud_flags, pd.DataFrame) else 0.0

    financial_exposure = 0.0
    if "Invoice_Difference" in merged.columns:
        financial_exposure = float(_safe_numeric(merged["Invoice_Difference"]).abs().sum())

    def _pct(v: float) -> float:
        if total_shipments <= 0:
            return 0.0
        return (v / total_shipments) * 100.0

    return {
        "total_shipments": total_shipments,
        "discrepancies": discrepancies,
        "discrepancies_pct": _pct(discrepancies),
        "high_risk": high_risk,
        "high_risk_pct": _pct(high_risk),
        "delayed": delayed,
        "delayed_pct": _pct(delayed),
        "fraud_cases": fraud_cases,
        "fraud_pct": _pct(fraud_cases),
        "financial_exposure": financial_exposure,
    }


def _add_logo(story: List[Any], styles: Dict[str, ParagraphStyle]) -> None:
    project_root = Path(__file__).resolve().parent.parent
    candidates = [
        project_root / "freightlens-logo.png",
        project_root / "assets" / "full_logo.png",
        project_root / "assets" / "logo.png",
    ]
    for path in candidates:
        if path.exists():
            with PILImage.open(path) as img:
                img = img.convert("RGBA")
                target_width_px = 240
                ratio = target_width_px / float(img.width or target_width_px)
                target_height_px = max(1, int(img.height * ratio))
                resized = img.resize((target_width_px, target_height_px), PILImage.Resampling.LANCZOS)
                logo_buf = BytesIO()
                resized.save(logo_buf, format="PNG", optimize=False)
                logo_buf.seek(0)
                width_in = target_width_px / 96.0
                height_in = target_height_px / 96.0
                logo = RLImage(logo_buf, width=width_in * inch, height=height_in * inch)
                logo.hAlign = "CENTER"
                story.append(logo)
            story.append(Spacer(1, 0.16 * inch))
            return
    story.append(Paragraph("FreightLens", styles["subtitle"]))


def _shipment_intelligence_chart(merged: pd.DataFrame, delay_trends: pd.DataFrame) -> RLImage:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    if not delay_trends.empty and {"Month", "mean"}.issubset(delay_trends.columns):
        d = delay_trends.copy().head(24)
        axes[0].plot(d["Month"].astype(str), _safe_numeric(d["mean"]), color="#2E7D32", linewidth=2)
        axes[0].set_title("Average Delay Trend", fontsize=10)
        axes[0].tick_params(axis="x", rotation=45, labelsize=8)
    else:
        axes[0].text(0.5, 0.5, "Delay trend data unavailable", ha="center", va="center")
        axes[0].set_axis_off()

    if "Delivery_Delay_Days" in merged.columns:
        delays = _downsample_series(_safe_numeric(merged["Delivery_Delay_Days"]))
        if len(delays) > 0:
            bins = min(20, max(8, int(np.sqrt(len(delays)))))
            axes[1].hist(delays, bins=bins, color="#4CAF50", alpha=0.85)
            axes[1].set_title("Delay Distribution", fontsize=10)
            axes[1].set_xlabel("Delay Days", fontsize=8)
            axes[1].set_ylabel("Shipments", fontsize=8)
    else:
        axes[1].text(0.5, 0.5, "Delay data unavailable", ha="center", va="center")
        axes[1].set_axis_off()

    return _figure_to_rl_image(fig, width_in=7.1, height_in=3.9)


def _bar_chart_from_df(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    top_n: int = 10,
    color: str = "#2E7D32",
) -> RLImage:
    fig, ax = plt.subplots(figsize=(8, 4))
    if df.empty or label_col not in df.columns or value_col not in df.columns:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.set_axis_off()
        return _figure_to_rl_image(fig)

    work = df[[label_col, value_col]].copy()
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna().sort_values(value_col, ascending=False).head(top_n)
    if work.empty:
        ax.text(0.5, 0.5, "No data available", ha="center", va="center")
        ax.set_axis_off()
        return _figure_to_rl_image(fig)

    y = np.arange(len(work))
    ax.barh(y, work[value_col].values, color=color, alpha=0.85)
    ax.set_yticks(y)
    ax.set_yticklabels(work[label_col].astype(str).values, fontsize=8)
    ax.invert_yaxis()
    ax.set_title(title, fontsize=11)
    ax.grid(axis="x", linestyle="--", alpha=0.25)
    return _figure_to_rl_image(fig, width_in=7.1, height_in=3.9)


def _financial_heatmap_chart(heatmap_data: pd.DataFrame) -> RLImage:
    fig, ax = plt.subplots(figsize=(8, 4))
    if heatmap_data.empty or not {"Transport_Company", "Lane", "Invoice_Difference"}.issubset(heatmap_data.columns):
        ax.text(0.5, 0.5, "Heatmap data unavailable", ha="center", va="center")
        ax.set_axis_off()
        return _figure_to_rl_image(fig)

    work = heatmap_data.copy()
    work["Invoice_Difference"] = pd.to_numeric(work["Invoice_Difference"], errors="coerce").fillna(0.0)
    top_carriers = (
        work.groupby("Transport_Company")["Invoice_Difference"].sum().abs().sort_values(ascending=False).head(8).index
    )
    top_lanes = work.groupby("Lane")["Invoice_Difference"].sum().abs().sort_values(ascending=False).head(10).index
    work = work[work["Transport_Company"].isin(top_carriers) & work["Lane"].isin(top_lanes)]
    if work.empty:
        ax.text(0.5, 0.5, "Heatmap data unavailable", ha="center", va="center")
        ax.set_axis_off()
        return _figure_to_rl_image(fig)

    pivot = work.pivot_table(
        index="Transport_Company",
        columns="Lane",
        values="Invoice_Difference",
        aggfunc="sum",
        fill_value=0.0,
    )
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlGn")
    ax.set_title("Financial Exposure Heatmap", fontsize=11)
    ax.set_yticks(np.arange(len(pivot.index)))
    ax.set_yticklabels([str(i)[:20] for i in pivot.index], fontsize=7)
    ax.set_xticks(np.arange(len(pivot.columns)))
    ax.set_xticklabels([str(c)[:14] for c in pivot.columns], rotation=45, ha="right", fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    return _figure_to_rl_image(fig, width_in=7.1, height_in=3.9)


def _fraud_distribution_chart(fraud_flags: pd.DataFrame) -> RLImage:
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    if fraud_flags.empty:
        for ax in axes:
            ax.text(0.5, 0.5, "No fraud flags available", ha="center", va="center")
            ax.set_axis_off()
        return _figure_to_rl_image(fig)

    if "Severity" in fraud_flags.columns:
        severity = fraud_flags["Severity"].astype(str).value_counts()
        axes[0].bar(severity.index, severity.values, color="#2E7D32")
        axes[0].set_title("Fraud Severity Distribution", fontsize=10)
        axes[0].tick_params(axis="x", rotation=20)
    else:
        axes[0].text(0.5, 0.5, "Severity data unavailable", ha="center", va="center")
        axes[0].set_axis_off()

    if "Reason" in fraud_flags.columns:
        reasons = fraud_flags["Reason"].astype(str).value_counts().head(8)
        axes[1].barh(np.arange(len(reasons)), reasons.values, color="#4CAF50")
        axes[1].set_yticks(np.arange(len(reasons)))
        axes[1].set_yticklabels(reasons.index, fontsize=7)
        axes[1].invert_yaxis()
        axes[1].set_title("Anomaly Reason Distribution", fontsize=10)
    else:
        axes[1].text(0.5, 0.5, "Reason data unavailable", ha="center", va="center")
        axes[1].set_axis_off()
    return _figure_to_rl_image(fig, width_in=7.1, height_in=3.9)


def _add_section_header(story: List[Any], title: str, styles: Dict[str, ParagraphStyle]) -> None:
    story.append(Paragraph(title, styles["section"]))
    story.append(HRFlowable(width="100%", thickness=0.8, color=colors.HexColor("#D0D7DE"), spaceBefore=2, spaceAfter=6))
    story.append(Spacer(1, SECTION_SPACER))


def _summary_box(text: str, styles: Dict[str, ParagraphStyle]) -> Table:
    table = Table([[Paragraph(text, styles["body"])]], colWidths=[7.1 * inch], hAlign="CENTER")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F7F6")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#D0D7DE")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return table


def generate_intelligence_report_pdf(
    merged: pd.DataFrame,
    context: Dict[str, Any],
    fraud_flags: pd.DataFrame,
    progress_callback: ProgressCallback = None,
) -> BytesIO:
    """
    Generate a multi-section enterprise PDF report and return it as BytesIO.

    Required sections:
    Executive Summary, Shipment Intelligence, Carrier Performance, Route Intelligence,
    Financial Risk, Fraud & Compliance, and AI Investigation Insights.
    """
    _emit_progress(progress_callback, 0.05, "Preparing report data")

    merged_df = _to_df(merged)
    context = context or {}
    fraud_df = _to_df(fraud_flags)
    if fraud_df.empty and not {"Shipment_ID", "Reason", "Severity"}.issubset(fraud_df.columns):
        fraud_df = pd.DataFrame(columns=["Shipment_ID", "Reason", "Severity"])

    delay_trends = _to_df(context.get("delay_trends"))
    carrier_risk = _to_df(context.get("carrier_risk"))
    lane_risk = _to_df(context.get("lane_risk"))
    heatmap_data = _to_df(context.get("heatmap_data"))
    insights_summary = context.get("insights_summary")
    insight_lines = _insights_as_text(insights_summary, max_items=8)
    kpis = _compute_kpis(merged_df, fraud_df)

    styles = _styles()
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=30,
        bottomMargin=28,
        title="FreightLens Intelligence Report",
        author="FreightLens AI Platform",
    )

    story: List[Any] = []
    _add_logo(story, styles)
    story.append(Paragraph("FreightLens Intelligence Report", styles["title"]))
    story.append(Paragraph("AI Powered Logistics Risk Platform", styles["subtitle"]))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["meta"]))
    story.append(Spacer(1, 0.20 * inch))

    _emit_progress(progress_callback, 0.15, "Writing executive summary")
    _add_section_header(story, "1. Executive Summary", styles)
    summary_sentence = (
        "FreightLens analysis of "
        f"{int(kpis['total_shipments']):,} shipments reveals that "
        f"{kpis['discrepancies_pct']:.1f}% show reconciliation discrepancies and "
        f"{kpis['fraud_pct']:.1f}% demonstrate fraud risk signals."
    )
    summary_text = summary_sentence
    if insight_lines:
        summary_text += f"<br/><br/><b>Top AI Insight:</b> {insight_lines[0]}"
    story.append(_summary_box(summary_text, styles))
    story.append(Spacer(1, 0.12 * inch))
    story.append(Paragraph(f"Total Shipments: {int(kpis['total_shipments']):,}", styles["kpi"]))
    story.append(Paragraph(f"Total Discrepancies: {int(kpis['discrepancies']):,}", styles["kpi"]))
    story.append(Paragraph(f"High Risk Shipments: {int(kpis['high_risk']):,}", styles["kpi"]))
    story.append(Paragraph(f"Delayed Shipments: {int(kpis['delayed']):,}", styles["kpi"]))
    story.append(Paragraph(f"Fraud Probability Indicators: {int(kpis['fraud_cases']):,} flagged records", styles["kpi"]))
    story.append(Paragraph(f"Financial Exposure: {kpis['financial_exposure']:,.2f}", styles["kpi"]))
    story.append(Spacer(1, CHART_SPACER))

    _emit_progress(progress_callback, 0.30, "Generating shipment intelligence visuals")
    _add_section_header(story, "2. Shipment Intelligence", styles)
    story.append(
        Paragraph(
            "Shipment delay trends, discrepancy indicators, and operational movement quality across the reporting window.",
            styles["body"],
        )
    )
    story.append(_shipment_intelligence_chart(merged_df, delay_trends))
    story.append(Spacer(1, CHART_SPACER))
    shipment_table_cols = [c for c in ["Month", "mean", "max", "count"] if c in delay_trends.columns]
    story.append(_table_from_df(delay_trends[shipment_table_cols] if shipment_table_cols else pd.DataFrame()))
    story.append(Spacer(1, CHART_SPACER))

    _emit_progress(progress_callback, 0.42, "Generating carrier performance intelligence")
    _add_section_header(story, "3. Carrier Performance Intelligence", styles)
    story.append(
        Paragraph(
            "Carrier risk profile with top risky carriers and reliability ranking based on shipment count and mean risk score.",
            styles["body"],
        )
    )
    story.append(_bar_chart_from_df(carrier_risk, "Transport_Company", "Mean_Risk_Score", "Top Carrier Risk Scores"))
    story.append(Spacer(1, CHART_SPACER))
    carrier_cols = [c for c in ["Transport_Company", "Shipment_Count", "Mean_Risk_Score", "Max_Risk_Score"] if c in carrier_risk.columns]
    story.append(_table_from_df(carrier_risk[carrier_cols] if carrier_cols else pd.DataFrame(), round_cols=["Mean_Risk_Score", "Max_Risk_Score"]))
    story.append(Spacer(1, CHART_SPACER))

    _emit_progress(progress_callback, 0.54, "Generating route intelligence")
    _add_section_header(story, "4. Route Intelligence", styles)
    story.append(
        Paragraph(
            "High-risk lanes and delay-prone corridors with route-level risk concentration for tactical intervention.",
            styles["body"],
        )
    )
    story.append(_bar_chart_from_df(lane_risk, "Lane", "Mean_Risk_Score", "Top High-Risk Routes"))
    story.append(Spacer(1, CHART_SPACER))
    route_cols = [c for c in ["Lane", "Shipment_Count", "Mean_Risk_Score", "Total_Invoice_Diff"] if c in lane_risk.columns]
    story.append(_table_from_df(lane_risk[route_cols] if route_cols else pd.DataFrame(), round_cols=["Mean_Risk_Score", "Total_Invoice_Diff"]))
    story.append(Spacer(1, CHART_SPACER))

    _emit_progress(progress_callback, 0.66, "Generating financial risk intelligence")
    _add_section_header(story, "5. Financial Risk Intelligence", styles)
    story.append(
        Paragraph(
            "Financial exposure by carrier and lane, including invoice mismatch aggregation and value-at-risk indicators.",
            styles["body"],
        )
    )
    story.append(_financial_heatmap_chart(heatmap_data))
    story.append(Spacer(1, CHART_SPACER))
    if "Invoice_Difference" in merged_df.columns:
        dist_df = pd.DataFrame(
            {"Invoice_Difference": _downsample_series(_safe_numeric(merged_df["Invoice_Difference"]).abs())}
        )
        story.append(_table_from_df(dist_df.describe().reset_index().rename(columns={"index": "Metric"}), max_rows=10))
        story.append(Spacer(1, CHART_SPACER))
    heatmap_cols = [c for c in ["Transport_Company", "Lane", "Invoice_Difference"] if c in heatmap_data.columns]
    story.append(_table_from_df(heatmap_data[heatmap_cols] if heatmap_cols else pd.DataFrame(), round_cols=["Invoice_Difference"]))
    story.append(Spacer(1, CHART_SPACER))

    _emit_progress(progress_callback, 0.78, "Generating fraud and compliance analysis")
    _add_section_header(story, "6. Fraud & Compliance Analysis", styles)
    story.append(
        Paragraph(
            "Flagged shipments, anomaly categories, and compliance risk signals to support targeted investigation.",
            styles["body"],
        )
    )
    story.append(_fraud_distribution_chart(fraud_df))
    story.append(Spacer(1, CHART_SPACER))
    fraud_cols = [c for c in ["Shipment_ID", "Reason", "Severity"] if c in fraud_df.columns]
    story.append(_table_from_df(fraud_df[fraud_cols] if fraud_cols else pd.DataFrame(), max_rows=20))
    story.append(Spacer(1, CHART_SPACER))

    _emit_progress(progress_callback, 0.88, "Adding AI investigation insights")
    _add_section_header(story, "7. AI Investigation Insights", styles)
    if insight_lines:
        for line in insight_lines[:8]:
            story.append(Paragraph(f"- {line}", styles["body"]))
    else:
        story.append(Paragraph("No AI-generated insights were available for this dataset.", styles["body"]))

    _emit_progress(progress_callback, 0.96, "Composing final PDF")
    doc.build(story, canvasmaker=_NumberedCanvas)
    buffer.seek(0)
    _emit_progress(progress_callback, 1.0, "Report ready")
    return buffer

