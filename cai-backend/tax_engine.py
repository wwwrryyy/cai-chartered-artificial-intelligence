"""Indian tax computation engine for CAI."""

from __future__ import annotations

from typing import Dict, List, Tuple

from config import (
    CESS_RATE,
    METRO_CITIES,
    NEW_REGIME_SLABS,
    OLD_REGIME_SLABS,
    REBATE_87A,
    STANDARD_DEDUCTION,
)


def apply_standard_deduction(income: float, regime: str) -> float:
    """Return standard deduction amount for given regime."""
    if income <= 0:
        return 0.0
    regime_key = (regime or "old").lower()
    return float(STANDARD_DEDUCTION.get(regime_key, 0.0))


def calculate_hra(
    basic_salary: float,
    hra_received: float,
    rent_paid: float,
    city_type: str | None = None,
    city_name: str | None = None,
) -> float:
    """Calculate HRA exemption for old regime.

    Exemption = min(
      actual HRA received,
      rent paid - 10% of basic,
      50% of basic for metro else 40% of basic
    )
    """
    basic = max(float(basic_salary or 0), 0.0)
    hra = max(float(hra_received or 0), 0.0)
    rent = max(float(rent_paid or 0), 0.0)

    if basic <= 0 or hra <= 0 or rent <= 0:
        return 0.0

    city_type_norm = (city_type or "").strip().lower()
    city_name_norm = (city_name or "").strip().lower()
    is_metro = city_type_norm == "metro" or city_name_norm in METRO_CITIES

    rent_minus_ten_percent_basic = max(rent - (0.10 * basic), 0.0)
    salary_ratio_component = 0.50 * basic if is_metro else 0.40 * basic

    return max(min(hra, rent_minus_ten_percent_basic, salary_ratio_component), 0.0)


def _get_slabs(regime: str) -> List[Tuple[float, float | None, float]]:
    return OLD_REGIME_SLABS if regime.lower() == "old" else NEW_REGIME_SLABS


def get_tax_slab(income: float, regime: str) -> Dict[str, float | str]:
    """Return applicable slab and rate for a given income."""
    slabs = _get_slabs(regime)
    inc = max(float(income or 0), 0.0)
    selected = slabs[0]
    for slab in slabs:
        lower, upper, rate = slab
        if upper is None:
            if inc > lower:
                selected = slab
                break
        elif lower < inc <= upper or (inc == 0 and lower == 0):
            selected = slab
            break
        elif inc > upper:
            selected = slab

    lower, upper, rate = selected
    return {
        "regime": regime.lower(),
        "income": inc,
        "slab_lower": lower,
        "slab_upper": upper if upper is not None else -1,
        "rate": rate,
    }


def _compute_slab_tax(taxable_income: float, slabs: List[Tuple[float, float | None, float]]) -> tuple[float, List[Dict[str, float]]]:
    taxable = max(float(taxable_income or 0), 0.0)
    total_tax = 0.0
    breakdown: List[Dict[str, float]] = []

    for lower, upper, rate in slabs:
        if taxable <= lower:
            continue

        upper_cap = taxable if upper is None else min(taxable, upper)
        taxed_amount = max(upper_cap - lower, 0.0)
        slab_tax = taxed_amount * rate
        if taxed_amount > 0:
            breakdown.append(
                {
                    "slab_from": lower,
                    "slab_to": upper if upper is not None else taxable,
                    "rate": rate,
                    "taxed_amount": taxed_amount,
                    "tax": slab_tax,
                }
            )
            total_tax += slab_tax

    return total_tax, breakdown


def apply_rebate(tax_before_rebate: float, taxable_income: float, regime: str) -> Dict[str, float]:
    """Apply Section 87A rebate rules."""
    rebate_rule = REBATE_87A[regime.lower()]
    income_limit = float(rebate_rule["income_limit"])
    max_rebate = float(rebate_rule["max_rebate"])

    if taxable_income <= income_limit:
        rebate = min(max_rebate, max(tax_before_rebate, 0.0))
    else:
        rebate = 0.0

    return {
        "rebate": rebate,
        "tax_after_rebate": max(tax_before_rebate - rebate, 0.0),
    }


def calculate_cess(tax_after_rebate: float) -> float:
    return max(float(tax_after_rebate or 0), 0.0) * CESS_RATE


def _allowed_new_regime_deductions(deductions: Dict[str, float]) -> Dict[str, float]:
    # New regime (as hackathon assumptions): allow only employer NPS contribution under 80CCD(2)
    allowed = {}
    nps_employer = float(deductions.get("80CCD(2)", 0.0))
    if nps_employer > 0:
        allowed["80CCD(2)"] = nps_employer
    return allowed


def compute_tax(income: float, deductions: Dict[str, float], regime: str = "old") -> Dict[str, object]:
    """Compute tax for old/new regime with detailed breakdown."""
    regime_key = (regime or "old").lower()
    gross_income = max(float(income or 0), 0.0)
    deductions_map = {k: max(float(v or 0), 0.0) for k, v in (deductions or {}).items()}

    standard_deduction = apply_standard_deduction(gross_income, regime_key)

    if regime_key == "new":
        allowed_deductions = _allowed_new_regime_deductions(deductions_map)
    else:
        allowed_deductions = deductions_map

    total_other_deductions = sum(allowed_deductions.values())
    taxable_income = max(gross_income - standard_deduction - total_other_deductions, 0.0)

    slabs = _get_slabs(regime_key)
    tax_before_rebate, slab_breakdown = _compute_slab_tax(taxable_income, slabs)
    rebate_info = apply_rebate(tax_before_rebate, taxable_income, regime_key)
    cess = calculate_cess(rebate_info["tax_after_rebate"])
    final_tax = rebate_info["tax_after_rebate"] + cess

    effective_tax_rate = (final_tax / gross_income * 100) if gross_income > 0 else 0.0

    return {
        "regime": regime_key,
        "gross_income": gross_income,
        "standard_deduction": standard_deduction,
        "allowed_deductions": allowed_deductions,
        "total_deductions": standard_deduction + total_other_deductions,
        "taxable_income": taxable_income,
        "slab_breakdown": slab_breakdown,
        "tax_before_rebate": tax_before_rebate,
        "rebate": rebate_info["rebate"],
        "tax_after_rebate": rebate_info["tax_after_rebate"],
        "cess": cess,
        "final_tax": final_tax,
        "effective_tax_rate": effective_tax_rate,
    }


def compare_regimes(income: float, deductions_old: Dict[str, float], deductions_new: Dict[str, float] | None = None) -> Dict[str, object]:
    """Compare old vs new regime and identify recommended option."""
    old_result = compute_tax(income=income, deductions=deductions_old, regime="old")
    new_result = compute_tax(income=income, deductions=deductions_new or {}, regime="new")

    if old_result["final_tax"] <= new_result["final_tax"]:
        recommended = "old"
        savings = new_result["final_tax"] - old_result["final_tax"]
    else:
        recommended = "new"
        savings = old_result["final_tax"] - new_result["final_tax"]

    return {
        "old_regime": old_result,
        "new_regime": new_result,
        "recommended_regime": recommended,
        "savings": savings,
    }


def estimate_no_planning_tax(income: float) -> Dict[str, object]:
    """Baseline tax estimate without claiming old regime deductions except standard deduction."""
    return compare_regimes(income=income, deductions_old={})