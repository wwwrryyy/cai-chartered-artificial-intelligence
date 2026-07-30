"""Session memory manager for Streamlit state."""

from __future__ import annotations

import copy
from typing import Any, Dict, List

import streamlit as st

DEFAULT_STATE = {
    "user_name": "",
    "financial_profile": {},
    "uploaded_documents": [],
    "uploaded_doc_text": "",
    "document_extraction": {},
    "deductions": [],
    "missing_evidence": [],
    "tax_result": {},
    "scenarios": [],
    "risk_assessment": {},
    "agent_trace": [],
    "final_summary": {},
}


def init_session() -> None:
    """Initialize all session keys used by the application."""
    for key, default_value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = copy.deepcopy(default_value)


def save_profile(profile: Dict[str, Any]) -> None:
    st.session_state.financial_profile = copy.deepcopy(profile)


def get_profile() -> Dict[str, Any]:
    return copy.deepcopy(st.session_state.get("financial_profile", {}))


def save_uploaded_documents(files: List[str], doc_text: str) -> None:
    st.session_state.uploaded_documents = list(files)
    st.session_state.uploaded_doc_text = doc_text or ""


def get_uploaded_doc_text() -> str:
    return st.session_state.get("uploaded_doc_text", "")


def save_document_extraction(extraction: Dict[str, Any]) -> None:
    st.session_state.document_extraction = copy.deepcopy(extraction)


def get_document_extraction() -> Dict[str, Any]:
    return copy.deepcopy(st.session_state.get("document_extraction", {}))


def save_deductions(deductions: List[Dict[str, Any]], missing_evidence: List[Dict[str, Any]]) -> None:
    st.session_state.deductions = copy.deepcopy(deductions)
    st.session_state.missing_evidence = copy.deepcopy(missing_evidence)


def get_deductions() -> List[Dict[str, Any]]:
    return copy.deepcopy(st.session_state.get("deductions", []))


def get_missing_evidence() -> List[Dict[str, Any]]:
    return copy.deepcopy(st.session_state.get("missing_evidence", []))


def save_tax_result(tax_data: Dict[str, Any]) -> None:
    st.session_state.tax_result = copy.deepcopy(tax_data)


def get_tax_result() -> Dict[str, Any]:
    return copy.deepcopy(st.session_state.get("tax_result", {}))


def save_scenarios(scenarios: List[Dict[str, Any]]) -> None:
    st.session_state.scenarios = copy.deepcopy(scenarios)


def get_scenarios() -> List[Dict[str, Any]]:
    return copy.deepcopy(st.session_state.get("scenarios", []))


def save_risk_assessment(risk: Dict[str, Any]) -> None:
    st.session_state.risk_assessment = copy.deepcopy(risk)


def get_risk_assessment() -> Dict[str, Any]:
    return copy.deepcopy(st.session_state.get("risk_assessment", {}))


def save_agent_trace(trace: List[Dict[str, Any]]) -> None:
    st.session_state.agent_trace = copy.deepcopy(trace)


def get_agent_trace() -> List[Dict[str, Any]]:
    return copy.deepcopy(st.session_state.get("agent_trace", []))


def save_final_summary(summary: Dict[str, Any]) -> None:
    st.session_state.final_summary = copy.deepcopy(summary)


def get_final_summary() -> Dict[str, Any]:
    return copy.deepcopy(st.session_state.get("final_summary", {}))


def clear_session() -> None:
    """Reset all stored session values."""
    for key in list(DEFAULT_STATE.keys()):
        st.session_state[key] = copy.deepcopy(DEFAULT_STATE[key])