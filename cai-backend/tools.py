"""Local tools that CAI agent can call."""

from __future__ import annotations

import re
from typing import Any, Dict, List

from config import DEDUCTION_LIMITS
from tax_engine import compute_tax, get_tax_slab

TAX_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "lookup_tax_slab",
        "description": "Look up applicable slab and rate for a given annual taxable income under old or new regime.",
        "parameters": {
            "type": "object",
            "properties": {
                "income": {"type": "number", "description": "Annual income in INR"},
                "regime": {"type": "string", "enum": ["old", "new"], "description": "Tax regime"},
            },
            "required": ["income", "regime"],
        },
    },
    {
        "name": "check_deduction_eligibility",
        "description": "Check deduction eligibility, limit, and allowed amount for a section like 80C or 80D.",
        "parameters": {
            "type": "object",
            "properties": {
                "section": {"type": "string", "description": "Section name e.g. 80C"},
                "amount": {"type": "number", "description": "Claimed amount"},
                "age": {"type": "integer", "description": "Taxpayer age"},
                "is_senior": {"type": "boolean", "description": "Is taxpayer senior citizen"},
                "parent_is_senior": {"type": "boolean", "description": "Are parents senior citizens"},
            },
            "required": ["section", "amount"],
        },
    },
    {
        "name": "compute_tax",
        "description": "Compute tax with deductions under specified regime and return detailed breakdown.",
        "parameters": {
            "type": "object",
            "properties": {
                "income": {"type": "number", "description": "Gross annual income in INR"},
                "deductions": {
                    "type": "object",
                    "description": "Mapping of section to deduction amount",
                    "additionalProperties": {"type": "number"},
                },
                "regime": {"type": "string", "enum": ["old", "new"], "description": "Tax regime"},
            },
            "required": ["income", "deductions", "regime"],
        },
    },
    {
        "name": "verify_document_claim",
        "description": "Verify if a textual document supports a claim and amount.",
        "parameters": {
            "type": "object",
            "properties": {
                "claim_type": {"type": "string", "description": "Claim label e.g. HRA, 80D, ELSS"},
                "doc_text": {"type": "string", "description": "Extracted document text"},
                "expected_amount": {"type": "number", "description": "Claim amount expected in INR"},
            },
            "required": ["claim_type", "doc_text"],
        },
    },
]


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, str):
            cleaned = value.replace(",", "").replace("₹", "").strip()
            return float(cleaned)
        return float(value)
    except (TypeError, ValueError):
        return default


def _lookup_slab(params: Dict[str, Any]) -> Dict[str, Any]:
    income = _to_float(params.get("income"), 0.0)
    regime = str(params.get("regime", "old")).lower()
    return get_tax_slab(income=income, regime=regime)


def _check_deduction(params: Dict[str, Any]) -> Dict[str, Any]:
    section = str(params.get("section", "")).strip()
    amount = max(_to_float(params.get("amount"), 0.0), 0.0)
    age = int(params.get("age") or 30)
    is_senior = bool(params.get("is_senior", age >= 60))
    parent_is_senior = bool(params.get("parent_is_senior", False))

    if section not in DEDUCTION_LIMITS:
        return {
            "section": section,
            "eligible": False,
            "allowed_amount": 0.0,
            "limit": 0.0,
            "reason": "Unknown section. Please verify claim manually.",
        }

    raw_limit = float(DEDUCTION_LIMITS[section]["limit"])
    limit = raw_limit

    if section == "80D":
        # Self/family: 25k (or 50k if senior) + parents: 25k (or 50k if senior)
        self_family_limit = 50000.0 if is_senior else 25000.0
        parents_limit = 50000.0 if parent_is_senior else 25000.0
        limit = self_family_limit + parents_limit

    allowed = min(amount, limit)
    eligible = amount > 0

    return {
        "section": section,
        "eligible": eligible,
        "claimed_amount": amount,
        "allowed_amount": allowed,
        "limit": limit,
        "remaining_capacity": max(limit - allowed, 0.0),
        "reason": "Within deduction rules" if eligible else "No claim amount provided",
    }


def _compute_tax(params: Dict[str, Any]) -> Dict[str, Any]:
    income = _to_float(params.get("income"), 0.0)
    regime = str(params.get("regime", "old")).lower()
    deductions = params.get("deductions", {}) or {}
    parsed_deductions = {str(k): max(_to_float(v, 0.0), 0.0) for k, v in deductions.items()}
    return compute_tax(income=income, deductions=parsed_deductions, regime=regime)


def _extract_amounts(text: str) -> List[float]:
    matches = re.findall(r"(?:₹|Rs\.?\s?)?\s*([0-9][0-9,]{2,})", text, flags=re.IGNORECASE)
    values = []
    for match in matches:
        cleaned = match.replace(",", "")
        try:
            values.append(float(cleaned))
        except ValueError:
            continue
    return values


def _verify_doc_claim(params: Dict[str, Any]) -> Dict[str, Any]:
    claim_type = str(params.get("claim_type", "")).strip().lower()
    doc_text = str(params.get("doc_text", ""))
    expected_amount = _to_float(params.get("expected_amount"), 0.0)
    doc_text_lower = doc_text.lower()

    keyword_map = {
        "hra": ["house rent allowance", "hra", "rent"],
        "80d": ["health insurance", "mediclaim", "80d", "premium"],
        "80c": ["ppf", "elss", "epf", "80c", "life insurance"],
        "80ccd(1b)": ["nps", "80ccd"],
        "80e": ["education loan", "interest certificate", "80e"],
        "80g": ["donation", "80g"],
    }

    keywords = keyword_map.get(claim_type, [claim_type])
    keyword_found = any(kw in doc_text_lower for kw in keywords if kw)

    amounts = _extract_amounts(doc_text)
    amount_found = False
    closest_amount = 0.0

    if expected_amount > 0 and amounts:
        closest_amount = min(amounts, key=lambda x: abs(x - expected_amount))
        amount_found = abs(closest_amount - expected_amount) <= max(1000.0, 0.1 * expected_amount)

    if keyword_found and (expected_amount <= 0 or amount_found):
        status = "verified"
        note = "Document supports this claim"
    elif keyword_found and expected_amount > 0 and not amount_found:
        status = "conflicting"
        note = "Claim keyword found, but expected amount not found in document"
    else:
        status = "needs_document"
        note = "No supporting evidence found in uploaded text"

    return {
        "claim_type": claim_type,
        "status": status,
        "keyword_found": keyword_found,
        "amount_found": amount_found,
        "closest_amount_detected": closest_amount,
        "expected_amount": expected_amount,
        "note": note,
    }


def execute_tool(name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a supported local tool by name."""
    tool_name = (name or "").strip()
    if tool_name == "lookup_tax_slab":
        return _lookup_slab(params)
    if tool_name == "check_deduction_eligibility":
        return _check_deduction(params)
    if tool_name == "compute_tax":
        return _compute_tax(params)
    if tool_name == "verify_document_claim":
        return _verify_doc_claim(params)

    return {"error": f"Unsupported tool: {tool_name}"}