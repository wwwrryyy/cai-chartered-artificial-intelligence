"""Gemma API wrapper with resilient JSON parsing and local fallbacks."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from google import genai
from dotenv import load_dotenv

from config import DEDUCTION_LIMITS, METRO_CITIES
from prompts import (
    AUDIT_PROMPT,
    DEDUCTION_PROMPT,
    EXTRACTION_PROMPT,
    SCENARIO_PROMPT,
    SUMMARY_PROMPT,
    SYSTEM_PROMPT,
    TOOL_PLANNER_PROMPT,
    TOOL_RESPONSE_SYNTHESIS_PROMPT,
)
from tax_engine import calculate_hra, compare_regimes, get_tax_slab

load_dotenv()


class GemmaConfigurationError(RuntimeError):
    """Raised when Gemma credentials or model setup fail."""


def _extract_text_from_response(response: Any) -> str:
    if response is None:
        return ""

    text = getattr(response, "text", "")
    if text:
        return str(text).strip()

    candidates = getattr(response, "candidates", None)
    if not candidates:
        return ""

    parts: List[str] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if not content:
            continue
        for part in getattr(content, "parts", []):
            value = getattr(part, "text", "")
            if value:
                parts.append(str(value))
    return "\n".join(parts).strip()


def _extract_json(text: str, default: Dict[str, Any] | None = None) -> Dict[str, Any]:
    if not text:
        return default or {}

    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "").replace("```", "").strip()

    try:
        obj = json.loads(cleaned)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        cleaned = cleaned

    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        block = match.group(0)
        try:
            obj = json.loads(block)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            block = block

    return default or {}


def _coerce_number(value: Any, default: float = 0.0) -> float:
    try:
        if isinstance(value, str):
            cleaned = value.replace("₹", "").replace(",", "").strip()
            return float(cleaned)
        return float(value)
    except (TypeError, ValueError):
        return default


def configure_gemma() -> genai.Client:
    """Configure and return Gemma client instance (new google-genai SDK)."""
    api_key = os.getenv("GEMMA_API_KEY", "").strip()
    if not api_key:
        raise GemmaConfigurationError(
            "GEMMA_API_KEY is not set. Please create .env from .env.example and add your API key."
        )

    return genai.Client(api_key=api_key)


def _invoke_model(prompt: str, images: List[str] = None, system_instruction: str | None = None) -> str:
    """Internal model invocation helper using local Ollama."""
    import requests
    model_name = os.getenv("GEMMA_MODEL", "qwen3-vl:4b").strip() or "qwen3-vl:4b"
    
    text_prompt = prompt
    if system_instruction:
        text_prompt = f"System: {system_instruction}\n\nUser: {prompt}"

    payload = {
        "model": model_name,
        "prompt": text_prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
            "num_ctx": 4096
        }
    }
    if images:
        payload["images"] = images

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as exc:
        print("Ollama Error:", exc)
        return ""


def call_gemma_simple(prompt: Any, images: List[str] = None, system_instruction: str | None = None) -> Dict[str, Any]:
    """Simple Gemma call that returns text and best-effort JSON parse."""
    try:
        text = _invoke_model(prompt=str(prompt), images=images, system_instruction=system_instruction)
        return {"ok": True, "text": text, "data": _extract_json(text, default={})}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "text": "", "data": {}, "error": str(exc)}


def call_gemma_with_tools(prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Ask Gemma to plan tool calls in JSON form.

    This is intentionally robust for hackathon demos and does not depend on SDK-specific
    function-calling primitives. Gemma still chooses tools based on tool schema.
    """
    tools_json = json.dumps(tools, ensure_ascii=False, indent=2)
    planner_prompt = (
        f"{TOOL_PLANNER_PROMPT}\n\n"
        f"Tool Schemas:\n{tools_json}\n\n"
        f"User Context:\n{prompt}\n"
    )

    result = call_gemma_simple(prompt=planner_prompt, system_instruction=SYSTEM_PROMPT)
    if result["ok"]:
        parsed = _extract_json(result.get("text", ""), default={})
        if isinstance(parsed.get("tool_calls"), list):
            return {
                "ok": True,
                "tool_calls": parsed.get("tool_calls", []),
                "planning_note": parsed.get("planning_note", ""),
                "raw_text": result.get("text", ""),
            }

    # Rule-based fallback planner
    lower = prompt.lower()
    fallback_calls = []
    if "slab" in lower or "regime" in lower:
        fallback_calls.append({"name": "lookup_tax_slab", "arguments": {"income": 1200000, "regime": "old"}})
    if "deduction" in lower or "80c" in lower or "hra" in lower:
        fallback_calls.append(
            {
                "name": "check_deduction_eligibility",
                "arguments": {"section": "80C", "amount": 80000, "age": 30, "is_senior": False},
            }
        )

    return {
        "ok": False,
        "tool_calls": fallback_calls,
        "planning_note": "Fallback planner used due model/tool parse issue.",
        "raw_text": result.get("error", "Gemma planner unavailable"),
    }


def _default_profile() -> Dict[str, Any]:
    return {
        "name": "",
        "employer_name": "",
        "city": "",
        "city_type": "non_metro",
        "annual_income": 0,
        "basic_salary": 0,
        "hra_received": 0,
        "rent_paid": 0,
        "investments": {"80C": 0, "80CCD(1B)": 0, "80D": 0, "ELSS": 0, "PPF": 0},
        "declared_deductions": {"80C": 0, "80D": 0},
        "savings_interest": 0,
        "education_loan_interest": 0,
        "donations": 0,
        "home_loan_interest": 0,
        "notes": [],
    }


def _profile_from_regex(raw_text: str) -> Dict[str, Any]:
    profile = _default_profile()
    text = raw_text or ""

    numbers = [float(x.replace(",", "")) for x in re.findall(r"(?:₹|Rs\.?\s?)?\s*([0-9][0-9,]{2,})", text)]

    def find_amount(keyword: str) -> float:
        pattern = rf"{keyword}[\s:=-]*[₹Rs\.,\s]*([0-9][0-9,]+)"
        match = re.search(pattern, text, flags=re.IGNORECASE)
        return float(match.group(1).replace(",", "")) if match else 0.0

    profile["annual_income"] = find_amount("annual|income|ctc|salary") or (max(numbers) if numbers else 0.0)
    profile["basic_salary"] = find_amount("basic")
    profile["hra_received"] = find_amount("hra|house rent allowance")
    profile["rent_paid"] = find_amount("rent")
    profile["investments"]["PPF"] = find_amount("ppf")
    profile["investments"]["ELSS"] = find_amount("elss")
    profile["investments"]["80D"] = find_amount("80d|health insurance|premium")
    profile["investments"]["80C"] = profile["investments"]["PPF"] + profile["investments"]["ELSS"]
    profile["declared_deductions"]["80C"] = profile["investments"]["80C"]
    profile["declared_deductions"]["80D"] = profile["investments"]["80D"]
    profile["savings_interest"] = find_amount("savings interest|interest")
    profile["education_loan_interest"] = find_amount("education loan")
    profile["donations"] = find_amount("donation|80g")
    profile["home_loan_interest"] = find_amount("home loan")

    city_match = re.search(r"\b(mumbai|delhi|chennai|kolkata|bengaluru|hyderabad|pune|coimbatore|ahmedabad)\b", text, flags=re.IGNORECASE)
    if city_match:
        city = city_match.group(1).title()
        profile["city"] = city
        profile["city_type"] = "metro" if city.lower() in METRO_CITIES else "non_metro"

    name_match = re.search(r"name\s*[:=-]\s*([A-Za-z ]{3,})", text, flags=re.IGNORECASE)
    if name_match:
        profile["name"] = name_match.group(1).strip()

    return profile


def extract_financial_data(raw_text: str, images: List[str] = None) -> Dict[str, Any]:
    """Extract structured financial profile from raw text/images using Gemma."""
    contents = f"{EXTRACTION_PROMPT}\n\nInput Text:\n{raw_text}"
    result = call_gemma_simple(prompt=contents, images=images, system_instruction=SYSTEM_PROMPT)

    if result["ok"] and result.get("data"):
        profile = _default_profile()
        model_data = result["data"]
        profile.update({k: v for k, v in model_data.items() if k in profile and k not in {"investments", "declared_deductions"}})

        inv = model_data.get("investments", {}) or {}
        profile["investments"].update({k: _coerce_number(v) for k, v in inv.items() if k in profile["investments"]})

        declared = model_data.get("declared_deductions", {}) or {}
        profile["declared_deductions"].update({k: _coerce_number(v) for k, v in declared.items() if k in profile["declared_deductions"]})

        for key in [
            "annual_income",
            "basic_salary",
            "hra_received",
            "rent_paid",
            "savings_interest",
            "education_loan_interest",
            "donations",
            "home_loan_interest",
        ]:
            profile[key] = _coerce_number(profile.get(key), 0.0)

        city = str(profile.get("city", "") or "")
        profile["city_type"] = "metro" if city.strip().lower() in METRO_CITIES else "non_metro"
        return profile

    return _profile_from_regex(raw_text)


def _local_discover_deductions(profile: Dict[str, Any]) -> Dict[str, Any]:
    annual_income = _coerce_number(profile.get("annual_income"), 0.0)
    investments = profile.get("investments", {}) or {}
    has_docs = bool(profile.get("has_documents", False))

    c80_amount = _coerce_number(investments.get("80C"), 0.0) or (
        _coerce_number(investments.get("PPF"), 0.0) + _coerce_number(investments.get("ELSS"), 0.0)
    )
    d80_amount = _coerce_number(investments.get("80D"), 0.0)
    nps_amount = _coerce_number(investments.get("80CCD(1B)"), 0.0)
    education = _coerce_number(profile.get("education_loan_interest"), 0.0)
    donation = _coerce_number(profile.get("donations"), 0.0)
    savings_interest = _coerce_number(profile.get("savings_interest"), 0.0)
    home_loan_interest = _coerce_number(profile.get("home_loan_interest"), 0.0)

    hra_amount = calculate_hra(
        basic_salary=_coerce_number(profile.get("basic_salary"), 0.0),
        hra_received=_coerce_number(profile.get("hra_received"), 0.0),
        rent_paid=_coerce_number(profile.get("rent_paid"), 0.0),
        city_type=profile.get("city_type", "non_metro"),
        city_name=profile.get("city", ""),
    )

    items: List[Dict[str, Any]] = []

    def add_item(section: str, claimed: float, eligible: float, remaining: float, reason: str, status: str) -> None:
        items.append(
            {
                "section": section,
                "category": DEDUCTION_LIMITS.get(section, {}).get("category", "Other"),
                "eligible_amount": round(max(eligible, 0.0), 2),
                "claimed_amount": round(max(claimed, 0.0), 2),
                "remaining_opportunity": round(max(remaining, 0.0), 2),
                "confidence": "high" if status == "verified" else "medium",
                "status": status,
                "action_needed": "Upload supporting proof" if status == "needs_document" else "No action",
                "reasoning": reason,
                "evidence_used": ["Uploaded documents"] if has_docs else ["User declaration"],
            }
        )

    c80_limit = float(DEDUCTION_LIMITS["80C"]["limit"])
    add_item(
        "80C",
        c80_amount,
        min(c80_amount, c80_limit),
        max(c80_limit - min(c80_amount, c80_limit), 0.0),
        "80C includes PPF/ELSS/EPF and has ₹1,50,000 cap.",
        "verified" if has_docs and c80_amount > 0 else ("needs_document" if c80_amount > 0 else "needs_document"),
    )

    nps_limit = float(DEDUCTION_LIMITS["80CCD(1B)"]["limit"])
    add_item(
        "80CCD(1B)",
        nps_amount,
        min(nps_amount, nps_limit),
        max(nps_limit - min(nps_amount, nps_limit), 0.0),
        "Additional NPS deduction available up to ₹50,000 under old regime.",
        "verified" if has_docs and nps_amount > 0 else "needs_document",
    )

    add_item(
        "80D",
        d80_amount,
        min(d80_amount, 100000),
        max(100000 - min(d80_amount, 100000), 0.0),
        "Health insurance premium deduction depends on age band.",
        "verified" if has_docs and d80_amount > 0 else ("needs_document" if d80_amount > 0 else "needs_document"),
    )

    add_item(
        "HRA",
        hra_amount,
        hra_amount,
        0.0,
        "HRA computed as minimum of actual HRA, rent minus 10% basic, and metro/non-metro salary ratio.",
        "verified" if has_docs and hra_amount > 0 else ("needs_document" if hra_amount > 0 else "needs_document"),
    )

    add_item(
        "80TTA",
        savings_interest,
        min(savings_interest, 10000),
        max(10000 - min(savings_interest, 10000), 0.0),
        "Savings account interest deduction up to ₹10,000 for non-senior taxpayers.",
        "verified" if has_docs and savings_interest > 0 else ("needs_document" if savings_interest > 0 else "needs_document"),
    )

    add_item(
        "80E",
        education,
        education,
        0.0,
        "Education loan interest can be fully claimed (up to 8 years) if loan proof exists.",
        "verified" if has_docs and education > 0 else ("needs_document" if education > 0 else "needs_document"),
    )

    add_item(
        "80G",
        donation,
        donation,
        0.0,
        "Donation deduction depends on institution eligibility and receipt details.",
        "verified" if has_docs and donation > 0 else ("needs_document" if donation > 0 else "needs_document"),
    )

    add_item(
        "24(b)",
        home_loan_interest,
        min(home_loan_interest, 200000),
        max(200000 - min(home_loan_interest, 200000), 0.0),
        "Home loan interest on self-occupied property capped at ₹2,00,000.",
        "verified" if has_docs and home_loan_interest > 0 else ("needs_document" if home_loan_interest > 0 else "needs_document"),
    )

    rebate_note = "Eligible under old regime if taxable income <= ₹5,00,000; under new regime if taxable income <= ₹12,00,000."
    items.append(
        {
            "section": "87A Rebate",
            "category": "Other",
            "eligible_amount": 60000 if annual_income <= 1200000 else 0,
            "claimed_amount": 0,
            "remaining_opportunity": 0,
            "confidence": "medium",
            "status": "verified",
            "action_needed": "Auto-applied during tax computation if eligible.",
            "reasoning": rebate_note,
            "evidence_used": ["Income level based rule"],
        }
    )

    missing_evidence = []
    for item in items:
        if item["status"] in {"needs_document", "conflicting"} and item["claimed_amount"] > 0:
            missing_evidence.append(
                {
                    "item": f"Section {item['section']}",
                    "status": item["status"],
                    "details": "Supporting document not found or incomplete.",
                }
            )

    return {
        "deductions": items,
        "missing_evidence": missing_evidence,
        "summary": "Deductions discovered using profile and Indian tax assumptions.",
    }


def discover_deductions(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Discover deductions proactively using Gemma with fallback logic."""
    prompt = f"{DEDUCTION_PROMPT}\n\nFinancial Profile JSON:\n{json.dumps(profile, ensure_ascii=False, indent=2)}"
    result = call_gemma_simple(prompt=prompt, system_instruction=SYSTEM_PROMPT)

    if result["ok"]:
        parsed = _extract_json(result.get("text", ""), default={})
        if isinstance(parsed.get("deductions"), list):
            return {
                "deductions": parsed.get("deductions", []),
                "missing_evidence": parsed.get("missing_evidence", []),
                "summary": parsed.get("summary", "Gemma deduction discovery complete."),
            }

    return _local_discover_deductions(profile)


def _local_scenarios(profile: Dict[str, Any], tax_data: Dict[str, Any]) -> Dict[str, Any]:
    income = _coerce_number(profile.get("annual_income"), 0.0)
    current_old_tax = _coerce_number(tax_data.get("old_regime", {}).get("final_tax"), 0.0)
    current_new_tax = _coerce_number(tax_data.get("new_regime", {}).get("final_tax"), 0.0)

    investments = profile.get("investments", {}) or {}
    c80_claimed = _coerce_number(investments.get("80C"), 0.0)
    remaining_80c = max(150000 - c80_claimed, 0.0)

    slab = get_tax_slab(income=income, regime="old")
    marginal_rate = float(slab.get("rate", 0.2))

    scenarios = []

    if remaining_80c > 0:
        add_amount = min(remaining_80c, 70000)
        est_impact = add_amount * marginal_rate
        scenarios.append(
            {
                "title": "Maximise 80C with ELSS/PPF",
                "action": f"Invest ₹{int(add_amount):,} more in ELSS/PPF before year-end.",
                "section": "80C",
                "additional_amount": add_amount,
                "estimated_tax_impact": est_impact,
                "net_savings": est_impact,
                "confidence": "high",
                "reasoning": "Your current 80C usage is below ₹1,50,000 limit.",
            }
        )

    nps_claimed = _coerce_number(investments.get("80CCD(1B)"), 0.0)
    remaining_nps = max(50000 - nps_claimed, 0.0)
    if remaining_nps > 0:
        est_impact = remaining_nps * marginal_rate
        scenarios.append(
            {
                "title": "Use extra NPS deduction",
                "action": f"Contribute ₹{int(remaining_nps):,} to NPS under Section 80CCD(1B).",
                "section": "80CCD(1B)",
                "additional_amount": remaining_nps,
                "estimated_tax_impact": est_impact,
                "net_savings": est_impact,
                "confidence": "medium",
                "reasoning": "This deduction is over and above 80C limit in old regime.",
            }
        )

    regime_diff = abs(current_old_tax - current_new_tax)
    recommended = tax_data.get("recommended_regime", "old")
    scenarios.append(
        {
            "title": "Choose the better tax regime",
            "action": f"File under {recommended.title()} Regime for this year.",
            "section": "Regime Selection",
            "additional_amount": 0,
            "estimated_tax_impact": regime_diff,
            "net_savings": regime_diff,
            "confidence": "high",
            "reasoning": "Direct computation shows this regime yields lower final tax.",
        }
    )

    while len(scenarios) < 3:
        scenarios.append(
            {
                "title": "Collect pending deduction documents",
                "action": "Upload receipts for HRA/insurance/donations to unlock pending deductions.",
                "section": "Documentation",
                "additional_amount": 0,
                "estimated_tax_impact": 0,
                "net_savings": 0,
                "confidence": "medium",
                "reasoning": "Missing proof can block deduction claims.",
            }
        )

    return {"scenarios": scenarios[:4]}


def generate_scenarios(profile: Dict[str, Any], tax_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate what-if planning scenarios with Gemma and fallback logic."""
    payload = {
        "profile": profile,
        "tax_data": tax_data,
    }
    prompt = f"{SCENARIO_PROMPT}\n\nInput:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    result = call_gemma_simple(prompt=prompt, system_instruction=SYSTEM_PROMPT)

    if result["ok"]:
        parsed = _extract_json(result.get("text", ""), default={})
        if isinstance(parsed.get("scenarios"), list) and len(parsed["scenarios"]) >= 3:
            return {"scenarios": parsed["scenarios"]}

    return _local_scenarios(profile, tax_data)


def _local_audit_risk(profile: Dict[str, Any]) -> Dict[str, Any]:
    income = max(_coerce_number(profile.get("annual_income"), 0.0), 1.0)
    deductions = profile.get("deduction_map", {}) or {}
    total_claims = sum(max(_coerce_number(v, 0.0), 0.0) for v in deductions.values())
    ratio = total_claims / income

    red_flags = []
    score = 20.0

    if ratio > 0.45:
        red_flags.append("High deduction-to-income ratio may invite scrutiny.")
        score += 35
    elif ratio > 0.30:
        red_flags.append("Moderately high deduction ratio; keep all proofs ready.")
        score += 20

    if _coerce_number(profile.get("rent_paid"), 0.0) > 0 and _coerce_number(profile.get("hra_received"), 0.0) == 0:
        red_flags.append("Rent claim present but HRA details missing.")
        score += 20

    if profile.get("missing_evidence_count", 0) >= 3:
        red_flags.append("Multiple deductions lack documentary evidence.")
        score += 20

    if score < 35:
        level = "Low"
    elif score < 70:
        level = "Medium"
    else:
        level = "High"

    if not red_flags:
        red_flags = ["No significant inconsistency detected from current data."]

    return {
        "risk_level": level,
        "risk_score": round(min(score, 100), 1),
        "red_flags": red_flags,
        "why": "Risk estimated from deduction ratio, claim consistency, and evidence completeness.",
        "mitigation_steps": [
            "Keep receipts and proofs in one folder for each section.",
            "Avoid overstating deductions beyond statutory limits.",
            "Cross-check Form 16, AIS, and bank statements before filing.",
        ],
    }


def audit_risk_analysis(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Assess audit risk using Gemma with deterministic fallback."""
    prompt = f"{AUDIT_PROMPT}\n\nProfile:\n{json.dumps(profile, ensure_ascii=False, indent=2)}"
    result = call_gemma_simple(prompt=prompt, system_instruction=SYSTEM_PROMPT)

    if result["ok"]:
        parsed = _extract_json(result.get("text", ""), default={})
        if parsed.get("risk_level"):
            return parsed

    return _local_audit_risk(profile)


def _local_summary(profile: Dict[str, Any], deductions: List[Dict[str, Any]], tax_result: Dict[str, Any]) -> Dict[str, Any]:
    income = _coerce_number(profile.get("annual_income"), 0.0)
    ded_total = sum(_coerce_number(item.get("eligible_amount"), 0.0) for item in deductions)

    old_tax = _coerce_number(tax_result.get("old_regime", {}).get("final_tax"), 0.0)
    new_tax = _coerce_number(tax_result.get("new_regime", {}).get("final_tax"), 0.0)
    best_tax = min(old_tax, new_tax) if old_tax and new_tax else old_tax or new_tax

    baseline = compare_regimes(income=income, deductions_old={})
    baseline_best = min(
        _coerce_number(baseline["old_regime"]["final_tax"], 0.0),
        _coerce_number(baseline["new_regime"]["final_tax"], 0.0),
    )
    tax_saved = max(baseline_best - best_tax, 0.0)

    pending_docs = sum(1 for item in deductions if item.get("status") == "needs_document")
    ca_review = sum(1 for item in deductions if str(item.get("confidence", "")).lower() == "low")

    return {
        "headline": "Your estimated tax plan is ready",
        "summary": (
            f"Based on your profile, estimated final tax is ₹{best_tax:,.0f}. "
            f"Potential deductions identified: ₹{ded_total:,.0f}. "
            f"Estimated savings vs no planning: ₹{tax_saved:,.0f}. "
            f"Pending documents: {pending_docs}. CA review items: {ca_review}."
        ),
        "next_steps": [
            "Upload pending proofs for medium-confidence claims.",
            "Complete remaining 80C/80CCD(1B) investments before 31 March if suitable.",
            "Use the recommended regime while filing ITR.",
        ],
    }


def generate_summary(profile: Dict[str, Any], deductions: List[Dict[str, Any]], tax_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate plain-language summary using Gemma with fallback."""
    payload = {
        "profile": profile,
        "deductions": deductions,
        "tax_data": tax_data,
    }
    prompt = f"{SUMMARY_PROMPT}\n\nInput:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    result = call_gemma_simple(prompt=prompt, system_instruction=SYSTEM_PROMPT)

    if result["ok"]:
        parsed = _extract_json(result.get("text", ""), default={})
        if parsed.get("summary"):
            return parsed

    return _local_summary(profile, deductions, tax_data)


def synthesize_tool_response(user_input: str, tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Use Gemma to convert tool outputs into user-friendly insights."""
    payload = {
        "user_input": user_input,
        "tool_results": tool_results,
    }
    prompt = (
        f"{TOOL_RESPONSE_SYNTHESIS_PROMPT}\n\n"
        f"Tool Results JSON:\n{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )
    result = call_gemma_simple(prompt=prompt, system_instruction=SYSTEM_PROMPT)
    if result["ok"]:
        parsed = _extract_json(result.get("text", ""), default={})
        if parsed.get("response"):
            return parsed

    return {
        "response": "Tool execution complete. Reviewed deductions, slabs, and tax impact using available data.",
        "confidence": "medium",
        "highlights": ["Gemma synthesis fallback used due API response format issue."],
    }