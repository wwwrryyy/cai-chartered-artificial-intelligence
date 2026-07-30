"""Streamlit entry point for CAI."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

from agent_core import CAIAgent
from config import (
    APP_NAME,
    APP_TAGLINE,
    CONFIDENCE_LABELS,
    SAMPLE_DOCUMENT_TEXT,
    SAMPLE_PROFILE,
    SECTION_CATEGORIES,
    STATUS_LABELS,
    format_inr,
)
from document_parser import (
    extract_financial_fields,
    parse_image,
    parse_pdf,
    validate_extraction,
)
from gemma_client import (
    audit_risk_analysis,
    discover_deductions,
    generate_scenarios,
    generate_summary,
)
from memory import (
    clear_session,
    get_agent_trace,
    get_deductions,
    get_document_extraction,
    get_final_summary,
    get_missing_evidence,
    get_profile,
    get_risk_assessment,
    get_scenarios,
    get_tax_result,
    init_session,
    save_agent_trace,
    save_deductions,
    save_document_extraction,
    save_final_summary,
    save_profile,
    save_risk_assessment,
    save_scenarios,
    save_tax_result,
    save_uploaded_documents,
)
from report_generator import (
    generate_pdf_report,
    get_download_button,
)
from tax_engine import compare_regimes
from tools import execute_tool

# ═══════════════════════════════════════════════════════════════════════════
# Page configuration
# ═══════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": f"CAI — {APP_TAGLINE}",
    },
)

# ═══════════════════════════════════════════════════════════════════════════
# Premium CSS — dark navy SaaS theme with gold accents
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<style>
    /* ── Root resets ───────────────────────────────────────────────── */
    header[data-testid="stHeader"] {visibility: hidden;}
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}

    /* ── Full-page dark navy gradient ──────────────────────────────── */
    .stApp {
        background: linear-gradient(160deg, #060d1a 0%, #0b1a30 30%, #0f1d3a 60%, #08142a 100%);
    }
    .main .block-container {
        padding-top: 1.5rem;
    }

    /* ── Sidebar ───────────────────────────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #08101f 0%, #0a1528 100%);
        border-right: 1px solid rgba(245, 158, 11, 0.12);
    }
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span {
        color: #c9d1d9 !important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f0f4f8 !important;
    }

    /* ── Brand header ──────────────────────────────────────────────── */
    .brand-header {
        background: linear-gradient(135deg, rgba(15,30,60,0.95) 0%, rgba(10,22,44,0.98) 100%);
        border: 1px solid rgba(245,158,11,0.18);
        border-radius: 16px;
        padding: 1.6rem 2rem 1.2rem 2rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.03);
    }
    .brand-title {
        font-size: 2.6rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #f59e0b 0%, #fbbf24 30%, #fcd34d 50%, #f59e0b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
    }
    .brand-tagline {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 400;
        letter-spacing: 0.2px;
    }

    /* ── Gold accent separators ────────────────────────────────────── */
    .gold-sep {
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, rgba(245,158,11,0.5) 20%, rgba(245,158,11,0.5) 80%, transparent 100%);
        margin: 1rem 0;
        border: none;
    }

    /* ── Deduction cards ───────────────────────────────────────────── */
    .deduction-card {
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
        border: 1px solid rgba(255,255,255,0.06);
        background: rgba(255,255,255,0.03);
        transition: all 0.2s ease;
    }
    .deduction-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .card-high { border-left: 4px solid #16a34a; }
    .card-medium { border-left: 4px solid #f59e0b; }
    .card-low { border-left: 4px solid #dc2626; }

    .card-section-label {
        font-weight: 700;
        font-size: 1.05rem;
        color: #e2e8f0;
        margin-bottom: 0.15rem;
    }
    .card-amount {
        font-weight: 700;
        font-size: 1.15rem;
        color: #fbbf24;
    }
    .card-badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-high { background: rgba(22,163,74,0.18); color: #4ade80; }
    .badge-medium { background: rgba(245,158,11,0.18); color: #fbbf24; }
    .badge-low { background: rgba(220,38,38,0.18); color: #f87171; }

    .status-verified { color: #4ade80; font-weight: 600; }
    .status-needs_document { color: #fbbf24; font-weight: 600; }
    .status-conflicting { color: #f87171; font-weight: 600; }

    /* ── Tax comparison panels ─────────────────────────────────────── */
    .compare-container {
        display: flex;
        gap: 1.2rem;
        margin: 1rem 0;
    }
    .compare-panel {
        flex: 1;
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        border: 1px solid rgba(255,255,255,0.08);
        background: rgba(255,255,255,0.03);
        box-shadow: 0 4px 16px rgba(0,0,0,0.25);
    }
    .compare-panel.winner {
        border-color: rgba(34,197,94,0.35);
        box-shadow: 0 0 20px rgba(34,197,94,0.1), 0 4px 16px rgba(0,0,0,0.25);
    }
    .compare-panel-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #e2e8f0;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid rgba(245,158,11,0.3);
    }
    .compare-amount {
        font-size: 2rem;
        font-weight: 800;
        color: #fbbf24;
    }
    .compare-winner-badge {
        display: inline-block;
        background: rgba(34,197,94,0.2);
        color: #4ade80;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 700;
        margin-top: 0.4rem;
    }

    /* ── Metric cards ──────────────────────────────────────────────── */
    div[data-testid="stMetric"] {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
        padding: 0.8rem 1rem !important;
    }
    div[data-testid="stMetric"] label {
        color: #94a3b8 !important;
        font-size: 0.82rem !important;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #f0f4f8 !important;
        font-size: 1.4rem !important;
        font-weight: 700 !important;
    }

    /* ── INR amounts everywhere ────────────────────────────────────── */
    .inr-amount {
        color: #fbbf24;
        font-weight: 700;
    }

    /* ── Buttons ───────────────────────────────────────────────────── */
    .stButton > button {
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: 1px solid rgba(245,158,11,0.3) !important;
        background: linear-gradient(135deg, rgba(245,158,11,0.12) 0%, rgba(217,119,6,0.08) 100%) !important;
        color: #fbbf24 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(245,158,11,0.22) 0%, rgba(217,119,6,0.15) 100%) !important;
        border-color: rgba(245,158,11,0.55) !important;
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(245,158,11,0.2);
    }
    .stButton > button:active {
        transform: translateY(0);
    }

    /* Primary action buttons (Find Deductions, Compute Tax, etc.) */
    button[kind="primary"] {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: #0f172a !important;
        font-weight: 700 !important;
        border: none !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%) !important;
        box-shadow: 0 4px 20px rgba(245,158,11,0.4) !important;
    }

    /* Download button special */
    .stDownloadButton > button {
        background: linear-gradient(135deg, rgba(34,197,94,0.15) 0%, rgba(22,163,74,0.1) 100%) !important;
        border: 1px solid rgba(34,197,94,0.35) !important;
        color: #4ade80 !important;
    }
    .stDownloadButton > button:hover {
        background: linear-gradient(135deg, rgba(34,197,94,0.25) 0%, rgba(22,163,74,0.2) 100%) !important;
        border-color: rgba(34,197,94,0.6) !important;
        box-shadow: 0 4px 16px rgba(34,197,94,0.2) !important;
    }

    /* ── Tab headers ───────────────────────────────────────────────── */
    button[data-baseweb="tab"] {
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        border-radius: 10px 10px 0 0 !important;
        color: #94a3b8 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #fbbf24 !important;
        border-bottom: 3px solid #f59e0b !important;
    }

    /* ── Expanders ─────────────────────────────────────────────────── */
    div[data-testid="stExpander"] {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 12px;
    }
    div[data-testid="stExpander"] summary {
        color: #c9d1d9 !important;
        font-weight: 600 !important;
    }

    /* ── Dataframes ────────────────────────────────────────────────── */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* ── Alerts ────────────────────────────────────────────────────── */
    div[data-testid="stAlert"] {
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,0.06) !important;
    }

    /* ── General typography ────────────────────────────────────────── */
    .stMarkdown, p, span, li {
        color: #c9d1d9;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #e2e8f0 !important;
    }
    .stCaption {
        color: #94a3b8 !important;
    }
    code {
        color: #fbbf24 !important;
        background: rgba(245,158,11,0.1) !important;
        border-radius: 4px;
        padding: 0.1rem 0.3rem;
    }

    /* ── File uploader ─────────────────────────────────────────────── */
    section[data-testid="stFileUploader"] {
        border: 2px dashed rgba(245,158,11,0.25) !important;
        border-radius: 14px !important;
        background: rgba(255,255,255,0.02) !important;
        padding: 0.5rem !important;
    }

    /* ── Divider ───────────────────────────────────────────────────── */
    hr {
        border-color: rgba(255,255,255,0.06) !important;
    }

    /* ── Text inputs ───────────────────────────────────────────────── */
    input, textarea, .stTextInput input, .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #e2e8f0 !important;
        border-radius: 8px !important;
    }
    input:focus, textarea:focus {
        border-color: rgba(245,158,11,0.5) !important;
        box-shadow: 0 0 0 2px rgba(245,158,11,0.15) !important;
    }
    label {
        color: #c9d1d9 !important;
        font-weight: 500 !important;
    }

    /* ── Number inputs ─────────────────────────────────────────────── */
    .stNumberInput input {
        background: rgba(255,255,255,0.05) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        color: #e2e8f0 !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

init_session()


# ═══════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _safe_float(value: Any) -> float:
    try:
        if isinstance(value, str):
            value = value.replace("₹", "").replace(",", "").strip()
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _determine_city_type(city: str) -> str:
    metro_cities = {"mumbai", "delhi", "chennai", "kolkata"}
    return "metro" if city.strip().lower() in metro_cities else "non_metro"


def _merge_profiles(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    merged = copy.deepcopy(base or {})
    incoming = incoming or {}
    for key, value in incoming.items():
        if key in {"investments", "declared_deductions"}:
            current = merged.get(key, {}) or {}
            for inner_key, inner_value in (value or {}).items():
                if isinstance(inner_value, (int, float)) and inner_value >= 0:
                    current[inner_key] = inner_value
            merged[key] = current
        else:
            if value not in (None, ""):
                merged[key] = value
    city = str(merged.get("city", "") or "")
    merged["city_type"] = _determine_city_type(city)
    return merged


def _show_profile_snapshot(profile: Dict[str, Any]) -> None:
    if not profile:
        st.info("No financial profile saved yet.")
        return
    col1, col2, col3 = st.columns(3)
    col1.metric("Annual Income", format_inr(profile.get("annual_income", 0)))
    col2.metric("Basic Salary", format_inr(profile.get("basic_salary", 0)))
    col3.metric("HRA Received", format_inr(profile.get("hra_received", 0)))
    st.caption(
        f"City: {profile.get('city', 'Not specified')} | "
        f"Rent Paid: {format_inr(profile.get('rent_paid', 0))} | "
        f"80C Declared: {format_inr((profile.get('investments', {}) or {}).get('80C', 0))}"
    )


def _render_profile_editor(profile: Dict[str, Any], key_prefix: str) -> Dict[str, Any]:
    draft = copy.deepcopy(profile or {})
    draft.setdefault("investments", {})
    col1, col2 = st.columns(2)
    with col1:
        draft["name"] = st.text_input("Name", value=str(draft.get("name", "")), key=f"{key_prefix}_name")
        draft["city"] = st.text_input("City", value=str(draft.get("city", "")), key=f"{key_prefix}_city")
        draft["age"] = int(st.number_input("Age", min_value=18, max_value=100, value=int(draft.get("age", 30) or 30), key=f"{key_prefix}_age"))
        draft["annual_income"] = st.number_input("Annual Income (₹)", min_value=0.0, value=float(draft.get("annual_income", 0) or 0), step=10000.0, key=f"{key_prefix}_income")
        draft["basic_salary"] = st.number_input("Basic Salary (₹)", min_value=0.0, value=float(draft.get("basic_salary", 0) or 0), step=10000.0, key=f"{key_prefix}_basic")
    with col2:
        draft["hra_received"] = st.number_input("HRA Received (₹)", min_value=0.0, value=float(draft.get("hra_received", 0) or 0), step=5000.0, key=f"{key_prefix}_hra")
        draft["rent_paid"] = st.number_input("Rent Paid (₹)", min_value=0.0, value=float(draft.get("rent_paid", 0) or 0), step=5000.0, key=f"{key_prefix}_rent")
        draft["savings_interest"] = st.number_input("Savings Interest (₹)", min_value=0.0, value=float(draft.get("savings_interest", 0) or 0), step=1000.0, key=f"{key_prefix}_tta")
        draft["education_loan_interest"] = st.number_input("Education Loan Interest (₹)", min_value=0.0, value=float(draft.get("education_loan_interest", 0) or 0), step=5000.0, key=f"{key_prefix}_80e")
    st.markdown("#### Investments / Claims")
    ic1, ic2, ic3 = st.columns(3)
    with ic1:
        draft["investments"]["80C"] = st.number_input("80C Total (₹)", min_value=0.0, value=float((draft.get("investments", {}) or {}).get("80C", 0) or 0), step=5000.0, key=f"{key_prefix}_80c")
        draft["investments"]["PPF"] = st.number_input("PPF (₹)", min_value=0.0, value=float((draft.get("investments", {}) or {}).get("PPF", 0) or 0), step=5000.0, key=f"{key_prefix}_ppf")
    with ic2:
        draft["investments"]["ELSS"] = st.number_input("ELSS (₹)", min_value=0.0, value=float((draft.get("investments", {}) or {}).get("ELSS", 0) or 0), step=5000.0, key=f"{key_prefix}_elss")
        draft["investments"]["80D"] = st.number_input("80D Health Insurance (₹)", min_value=0.0, value=float((draft.get("investments", {}) or {}).get("80D", 0) or 0), step=5000.0, key=f"{key_prefix}_80d")
    with ic3:
        draft["investments"]["80CCD(1B)"] = st.number_input("80CCD(1B) NPS (₹)", min_value=0.0, value=float((draft.get("investments", {}) or {}).get("80CCD(1B)", 0) or 0), step=5000.0, key=f"{key_prefix}_nps")
        draft["donations"] = st.number_input("Donations 80G (₹)", min_value=0.0, value=float(draft.get("donations", 0) or 0), step=1000.0, key=f"{key_prefix}_80g")
    draft["declared_deductions"] = {
        "80C": float((draft.get("investments", {}) or {}).get("80C", 0) or 0),
        "80D": float((draft.get("investments", {}) or {}).get("80D", 0) or 0),
    }
    draft["city_type"] = _determine_city_type(str(draft.get("city", "")))
    return draft


def _build_verified_deduction_map(deductions: List[Dict[str, Any]]) -> Dict[str, float]:
    deduction_map: Dict[str, float] = {}
    excluded_sections = {"87A Rebate", "LTA"}
    for item in deductions:
        section = str(item.get("section", "")).strip()
        status = str(item.get("status", "")).strip().lower()
        if section in excluded_sections or status != "verified":
            continue
        amount = _safe_float(item.get("eligible_amount", 0))
        if amount > 0:
            deduction_map[section] = amount
    return deduction_map


def _cross_verify_claims(
    deductions: List[Dict[str, Any]],
    doc_text: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    updated: List[Dict[str, Any]] = []
    missing: List[Dict[str, Any]] = []
    for item in deductions:
        row = copy.deepcopy(item)
        section = str(row.get("section", "")).strip()
        claimed_amount = _safe_float(row.get("claimed_amount", 0))
        if section in {"87A Rebate", "LTA"}:
            updated.append(row)
            continue
        if claimed_amount > 0 and doc_text.strip():
            verification = execute_tool("verify_document_claim", {"claim_type": section, "doc_text": doc_text, "expected_amount": claimed_amount})
            status = verification.get("status", row.get("status", "needs_document"))
            row["status"] = status
            row["confidence"] = "high" if status == "verified" else ("medium" if status == "needs_document" else "low")
            row["verification_note"] = verification.get("note", "")
        elif claimed_amount > 0 and not doc_text.strip():
            row["status"] = "needs_document"
            row["confidence"] = "medium"
            row["verification_note"] = "No uploaded document text found for verification."
        if row.get("status") in {"needs_document", "conflicting"} and claimed_amount > 0:
            missing.append({"item": f"Section {section}", "status": row.get("status"), "details": row.get("verification_note") or row.get("action_needed", "Upload proof")})
        updated.append(row)
    return updated, missing


def _render_deduction_panel(deductions: List[Dict[str, Any]]) -> None:
    if not deductions:
        st.info("No deductions discovered yet.")
        return

    for category in SECTION_CATEGORIES:
        category_items = [d for d in deductions if d.get("category") == category]
        if not category_items:
            continue

        st.markdown(f'<div class="gold-sep"></div>', unsafe_allow_html=True)
        st.markdown(f"### {category}")

        for item in category_items:
            confidence = str(item.get("confidence", "medium")).lower()
            card_class = f"card-{confidence}"
            badge_class = f"badge-{confidence}"
            status = str(item.get("status", ""))
            status_class = f"status-{status}"

            section_label = item.get("section", "-")
            eligible = format_inr(item.get("eligible_amount", 0))
            claimed = format_inr(item.get("claimed_amount", 0))
            remaining = format_inr(item.get("remaining_opportunity", 0))
            confidence_label = CONFIDENCE_LABELS.get(confidence, "Medium")
            status_label = STATUS_LABELS.get(status, item.get("status", "-"))
            action = item.get("action_needed", "")

            st.markdown(
                f"""
                <div class="deduction-card {card_class}">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:0.4rem;">
                        <div>
                            <div class="card-section-label">Section {section_label}</div>
                            <div style="font-size:0.8rem; color:#94a3b8;">{action}</div>
                        </div>
                        <div style="text-align:right;">
                            <div class="card-amount">{eligible}</div>
                            <div style="font-size:0.75rem; color:#94a3b8;">Claimed: {claimed} | Left: {remaining}</div>
                        </div>
                    </div>
                    <div style="margin-top:0.5rem; display:flex; gap:0.6rem; align-items:center; flex-wrap:wrap;">
                        <span class="{status_class}">{status_label}</span>
                        <span class="card-badge {badge_class}">{confidence_label}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.expander("Why this?"):
                st.write(item.get("reasoning", "No reasoning provided"))
                evidence = item.get("evidence_used", []) or []
                if evidence:
                    st.write("Evidence:", ", ".join(evidence))
                if item.get("verification_note"):
                    st.write("Verification:", item["verification_note"])


def _render_tax_comparison(tax_result: Dict[str, Any]) -> None:
    if not tax_result:
        st.info("Tax comparison not computed yet.")
        return

    old = tax_result.get("old_regime", {})
    new = tax_result.get("new_regime", {})
    recommended = str(tax_result.get("recommended_regime", "old")).lower()
    savings = format_inr(tax_result.get("savings", 0))

    st.markdown('<div class="gold-sep"></div>', unsafe_allow_html=True)
    st.markdown("### Old vs New Regime Comparison")

    c1, c2 = st.columns(2)
    with c1:
        is_winner = recommended == "old"
        winner_markup = '<span class="compare-winner-badge">Recommended</span>' if is_winner else ""
        st.markdown(
            f"""
            <div class="compare-panel {'winner' if is_winner else ''}">
                <div class="compare-panel-header">Old Regime</div>
                <div class="compare-amount">{format_inr(old.get("final_tax", 0))}</div>
                <div style="color:#94a3b8; font-size:0.85rem; margin-top:0.2rem;">
                    Effective Rate: {old.get('effective_tax_rate', 0):.1f}%
                </div>
                {winner_markup}
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        is_winner = recommended == "new"
        winner_markup = '<span class="compare-winner-badge">Recommended</span>' if is_winner else ""
        st.markdown(
            f"""
            <div class="compare-panel {'winner' if is_winner else ''}">
                <div class="compare-panel-header">New Regime</div>
                <div class="compare-amount">{format_inr(new.get("final_tax", 0))}</div>
                <div style="color:#94a3b8; font-size:0.85rem; margin-top:0.2rem;">
                    Effective Rate: {new.get('effective_tax_rate', 0):.1f}%
                </div>
                {winner_markup}
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        f'<div style="text-align:center; margin:0.8rem 0; font-size:1.1rem; font-weight:700; color:#4ade80;">'
        f'You save <span class="inr-amount">{savings}</span> with the <strong>{recommended.title()} Regime</strong>'
        f'</div>',
        unsafe_allow_html=True,
    )

    breakdown_rows = []
    for regime_label, data in [("Old", old), ("New", new)]:
        breakdown_rows.extend([
            {"Regime": regime_label, "Stage": "Gross Income", "Amount": data.get("gross_income", 0)},
            {"Regime": regime_label, "Stage": "Standard Deduction", "Amount": -data.get("standard_deduction", 0)},
            {"Regime": regime_label, "Stage": "Other Deductions", "Amount": -(sum((data.get("allowed_deductions", {}) or {}).values()))},
            {"Regime": regime_label, "Stage": "Taxable Income", "Amount": data.get("taxable_income", 0)},
            {"Regime": regime_label, "Stage": "Tax Before Rebate", "Amount": data.get("tax_before_rebate", 0)},
            {"Regime": regime_label, "Stage": "Rebate", "Amount": -data.get("rebate", 0)},
            {"Regime": regime_label, "Stage": "Cess", "Amount": data.get("cess", 0)},
            {"Regime": regime_label, "Stage": "Final Tax", "Amount": data.get("final_tax", 0)},
        ])

    df = pd.DataFrame(breakdown_rows)
    df["Amount"] = df["Amount"].apply(lambda x: f"₹{x:,.0f}")
    st.markdown("#### Tax Breakdown")
    st.dataframe(df, use_container_width=True, hide_index=True)


def _apply_scenario(profile: Dict[str, Any], scenario: Dict[str, Any]) -> Dict[str, Any]:
    updated = copy.deepcopy(profile)
    section = str(scenario.get("section", "")).strip()
    amount = _safe_float(scenario.get("additional_amount", 0))
    updated.setdefault("investments", {})
    if section in {"80C", "80CCD(1B)", "80D"} and amount > 0:
        updated["investments"][section] = _safe_float(updated["investments"].get(section, 0)) + amount
    return updated


# ═══════════════════════════════════════════════════════════════════════════
# Brand header
# ═══════════════════════════════════════════════════════════════════════════
st.markdown(
    f"""
    <div class="brand-header">
        <div class="brand-title">{APP_NAME} <span style="font-size:1.8rem;">🇮🇳</span></div>
        <div class="brand-tagline">{APP_TAGLINE}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

profile = get_profile()

# ═══════════════════════════════════════════════════════════════════════════
# Sidebar
# ═══════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### Session")
    user_name = st.text_input("Your Name", value=st.session_state.get("user_name", ""), placeholder="e.g. Rahul")
    st.session_state.user_name = user_name

    if user_name:
        profile["name"] = user_name
        save_profile(profile)

    tax_result_sidebar = get_tax_result()
    if user_name and tax_result_sidebar:
        st.success(f"Welcome back, {user_name}. Your tax estimate is ready.")

    income = _safe_float(profile.get("annual_income", 0))
    if income > 0:
        bracket = "Below ₹5L" if income < 500000 else ("₹5L - ₹12L" if income < 1200000 else "Above ₹12L")
        st.write(f"Income Bracket: **{bracket}**")

    deductions_count = len(get_deductions())
    st.write(f"Deductions analysed: **{deductions_count}**")

    st.markdown('<div class="gold-sep"></div>', unsafe_allow_html=True)

    if st.button("Reset Session", use_container_width=True):
        clear_session()
        st.success("Session reset complete.")
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════
# Tabs
# ═══════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "📄 Document Upload",
    "💬 Talk to CAI",
    "🔍 Discover Deductions",
    "📊 Tax Summary & Report",
])

# ── TAB 1: Document Upload ───────────────────────────────────────────────
with tab1:
    st.subheader("Upload Salary, Investment, Rent, Insurance Documents")
    uploaded_files = st.file_uploader(
        "Upload PDF, PNG, JPG documents",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )

    cta1, cta2 = st.columns(2)
    with cta1:
        if st.button("Load Sample Data", use_container_width=True):
            demo_profile = copy.deepcopy(SAMPLE_PROFILE)
            save_profile(demo_profile)
            save_document_extraction(demo_profile)
            save_uploaded_documents(["sample_document.txt"], SAMPLE_DOCUMENT_TEXT)
            st.success("Sample profile loaded for demo flow.")
    with cta2:
        extract_clicked = st.button("Extract from Uploaded Files", use_container_width=True)

    if extract_clicked:
        if not uploaded_files:
            st.error("Please upload at least one document before extraction.")
        else:
            all_text = []
            file_names = []
            with st.spinner("CAI is reading documents with Gemma"):
                for uploaded in uploaded_files:
                    file_names.append(uploaded.name)
                    file_bytes = uploaded.getvalue()
                    extracted_text = parse_pdf(file_bytes) if (uploaded.type == "application/pdf" or uploaded.name.lower().endswith(".pdf")) else parse_image(file_bytes)
                    all_text.append(f"--- {uploaded.name} ---\n{extracted_text}")
                combined_text = "\n\n".join(all_text).strip()
                if not combined_text:
                    st.error("Text extraction did not return content. Please try clearer files or use Talk to CAI tab.")
                else:
                    extracted_profile = extract_financial_fields(combined_text)
                    extracted_profile["has_documents"] = True
                    valid, issues = validate_extraction(extracted_profile)
                    save_document_extraction(extracted_profile)
                    save_uploaded_documents(file_names, combined_text)
                    if valid:
                        st.success("Extraction completed.")
                    else:
                        st.warning("Extraction completed with a few warnings.")
                    for issue in issues:
                        st.caption(f"  • {issue}")

    extraction = get_document_extraction()
    if extraction:
        st.markdown("### Extracted Financial Summary")
        _show_profile_snapshot(extraction)
        with st.expander("View structured extraction JSON"):
            st.json(extraction)
        if st.button("Confirm Extraction", use_container_width=True):
            merged = _merge_profiles(get_profile(), extraction)
            merged["has_documents"] = True
            save_profile(merged)
            st.success("Extraction saved to session profile.")

# ── TAB 2: Talk to CAI ────────────────────────────────────────────────
with tab2:
    st.subheader("Describe your finances in plain language")
    st.caption("Example: I earn ₹12 lakhs, pay ₹20k monthly rent in Chennai, invested ₹50k in PPF.")
    plain_input = st.text_area(
        "Tell CAI about your income, investments, rent, insurance, loans, and donations",
        height=160,
        key="plain_language_input",
    )
    if st.button("Analyze My Finances", use_container_width=True):
        if not plain_input.strip():
            st.error("Please enter your financial details in plain language.")
        else:
            with st.spinner("Gemma is converting your text into a financial profile"):
                try:
                    parsed_profile = extract_financial_fields(plain_input)
                    st.session_state["nl_profile_draft"] = parsed_profile
                    st.success("Profile analysed successfully.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Could not analyse input: {exc}")

    draft_profile = st.session_state.get("nl_profile_draft") or get_profile()
    if draft_profile:
        st.markdown("### Structured Profile (Editable)")
        edited_profile = _render_profile_editor(draft_profile, key_prefix="talk")
        if st.button("Save Profile", use_container_width=True):
            merged = _merge_profiles(get_profile(), edited_profile)
            save_profile(merged)
            st.success("Profile saved. Move to Discover Deductions tab.")

# ── TAB 3: Discover Deductions ────────────────────────────────────────────
with tab3:
    st.subheader("Proactive Deduction Discovery")
    profile = get_profile()
    _show_profile_snapshot(profile)

    if not profile or _safe_float(profile.get("annual_income", 0)) <= 0:
        st.info("Please upload documents or use Talk to CAI first.")
    else:
        agent = CAIAgent()

        if st.button("Find All Deductions", use_container_width=True, type="primary"):
            with st.spinner("Gemma is discovering all eligible deductions"):
                try:
                    profile_for_discovery = copy.deepcopy(profile)
                    profile_for_discovery["has_documents"] = bool(st.session_state.get("uploaded_doc_text", "").strip())
                    deduction_output = discover_deductions(profile_for_discovery)
                    deductions = deduction_output.get("deductions", [])
                    missing = deduction_output.get("missing_evidence", [])
                    verified_deductions, auto_missing = _cross_verify_claims(
                        deductions=deductions,
                        doc_text=st.session_state.get("uploaded_doc_text", ""),
                    )
                    combined_missing = missing + [m for m in auto_missing if m not in missing]
                    save_deductions(verified_deductions, combined_missing)
                    deduction_map_for_agent = _build_verified_deduction_map(verified_deductions)
                    profile_for_agent = copy.deepcopy(profile)
                    profile_for_agent["deduction_map"] = deduction_map_for_agent
                    agent_output = agent.run(
                        user_input="Analyse deductions, slabs, and tax tools for this profile",
                        financial_profile=profile_for_agent,
                    )
                    save_agent_trace(agent_output.get("trace", []))
                    st.success("Deductions discovered with evidence checks.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Deductions discovery failed: {exc}")

        deductions = get_deductions()
        _render_deduction_panel(deductions)

        st.markdown("### Missing Evidence Detector")
        missing_evidence = get_missing_evidence()
        if missing_evidence:
            for item in missing_evidence:
                status = item.get("status", "needs_document")
                label = STATUS_LABELS.get(status, status)
                st.warning(f"{label} — {item.get('item', '-')}: {item.get('details', '-')}")
        else:
            st.success("All currently claimed items are verified or not yet claimed.")

        if st.button("Compute Tax", use_container_width=True, type="primary"):
            with st.spinner("Computing old vs new regime tax"):
                try:
                    verified_map = _build_verified_deduction_map(get_deductions())
                    annual_income = _safe_float(profile.get("annual_income", 0))
                    tax_result = compare_regimes(income=annual_income, deductions_old=verified_map)
                    save_tax_result(tax_result)
                    risk_payload = copy.deepcopy(profile)
                    risk_payload["deduction_map"] = verified_map
                    risk_payload["missing_evidence_count"] = len(get_missing_evidence())
                    risk = audit_risk_analysis(risk_payload)
                    save_risk_assessment(risk)
                    summary = generate_summary(profile, get_deductions(), tax_result)
                    save_final_summary(summary)
                    st.success("Tax comparison and risk analysis completed.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Tax computation failed: {exc}")

        tax_result = get_tax_result()
        if tax_result:
            st.markdown('<div class="gold-sep"></div>', unsafe_allow_html=True)
            _render_tax_comparison(tax_result)

        risk = get_risk_assessment()
        if risk:
            st.markdown("### Audit Risk Flag")
            risk_level = risk.get("risk_level", "Unknown")
            risk_score = risk.get("risk_score", 0)
            if str(risk_level).lower() == "low":
                st.success(f"Risk: {risk_level} ({risk_score}/100)")
            elif str(risk_level).lower() == "medium":
                st.warning(f"Risk: {risk_level} ({risk_score}/100)")
            else:
                st.error(f"Risk: {risk_level} ({risk_score}/100)")
            st.write(risk.get("why", ""))
            for flag in risk.get("red_flags", []) or []:
                st.write(f"  • {flag}")
            st.markdown("**How to reduce risk:**")
            for step in risk.get("mitigation_steps", []) or []:
                st.write(f"- {step}")

# ── TAB 4: Tax Summary & Report ──────────────────────────────────────────
with tab4:
    st.subheader("Tax Summary, Scenarios, and Export")
    profile = get_profile()
    deductions = get_deductions()
    tax_result = get_tax_result()
    risk = get_risk_assessment()

    if not tax_result:
        st.info("Compute tax from Discover Deductions tab first.")
    else:
        _render_tax_comparison(tax_result)

        st.markdown("### Tax Planning Scenarios (What-If Mode)")
        st.markdown('<div class="gold-sep"></div>', unsafe_allow_html=True)

        if st.button("Generate Scenarios", use_container_width=True, type="primary"):
            with st.spinner("Gemma is preparing actionable what-if scenarios"):
                try:
                    scenarios_payload = generate_scenarios(profile, tax_result)
                    save_scenarios(scenarios_payload.get("scenarios", []))
                    st.success("Scenario recommendations generated.")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Scenario generation failed: {exc}")

        scenarios = get_scenarios()
        if scenarios:
            for idx, scenario in enumerate(scenarios, start=1):
                confidence = str(scenario.get("confidence", "medium")).lower()
                badge_class = f"badge-{confidence}"
                with st.container(border=True):
                    st.markdown(f"**{idx}. {scenario.get('title', 'Scenario')}**")
                    st.write(scenario.get("action", ""))
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Tax Impact", format_inr(scenario.get("estimated_tax_impact", 0)))
                    c2.metric("Net Savings", format_inr(scenario.get("net_savings", 0)))
                    c3.markdown(f"Confidence: <span class='card-badge {badge_class}'>{CONFIDENCE_LABELS.get(confidence, 'Medium')}</span>", unsafe_allow_html=True)
                    with st.expander("Why?"):
                        st.write(scenario.get("reasoning", "No reasoning provided"))
                    if st.button(f"Apply Scenario {idx}", key=f"apply_scenario_{idx}"):
                        updated_profile = _apply_scenario(profile, scenario)
                        save_profile(updated_profile)
                        verified_map = _build_verified_deduction_map(deductions)
                        section = str(scenario.get("section", "")).strip()
                        add_amount = _safe_float(scenario.get("additional_amount", 0))
                        if section in {"80C", "80CCD(1B)", "80D"} and add_amount > 0:
                            verified_map[section] = _safe_float(verified_map.get(section, 0)) + add_amount
                        recomputed = compare_regimes(
                            income=_safe_float(updated_profile.get("annual_income", 0)),
                            deductions_old=verified_map,
                        )
                        save_tax_result(recomputed)
                        st.success("Scenario applied and tax recomputed.")

        st.markdown("### Final Plain-Language Summary")
        summary = get_final_summary()
        if not summary:
            with st.spinner("Gemma is generating your summary"):
                summary = generate_summary(profile, deductions, tax_result)
                save_final_summary(summary)
        st.info(summary.get("summary", "Summary unavailable"))
        st.markdown("**What's Next**")
        for step in summary.get("next_steps", []) or []:
            st.write(f"- {step}")

        st.markdown("### Export Full Report")
        st.markdown('<div class="gold-sep"></div>', unsafe_allow_html=True)

        pdf_bytes = generate_pdf_report(
            profile=profile,
            deductions=deductions,
            tax=tax_result,
            scenarios=get_scenarios(),
            risk=risk,
            missing_evidence=get_missing_evidence(),
        )
        get_download_button(
            content=pdf_bytes,
            filename="cai_report.pdf",
            label="📥 Download Tax Report (PDF)",
            mime="application/pdf",
        )

        if st.button("Reset Session", use_container_width=True, key="reset_tab4"):
            clear_session()
            st.success("Session reset complete.")
            st.rerun()

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("🧠 Agent Trace (Gemma Tool Calls)"):
    trace = get_agent_trace()
    if trace:
        st.json(trace)
    else:
        st.caption("No agent tool trace yet. Use 'Find All Deductions' in Tab 3.")