"""Configuration constants for CAI."""

from __future__ import annotations

from typing import Dict, List, Tuple

APP_NAME = "CAI"
APP_TAGLINE = "Finding every deduction, missing nothing — powered by Gemma 4"
CURRENCY_SYMBOL = "₹"
DATE_FORMAT = "%d/%m/%Y"

METRO_CITIES = {"mumbai", "delhi", "chennai", "kolkata"}

# Tax slabs for FY 2025-26 (AY 2026-27 assumptions)
# Tuple format: (lower_limit_inclusive, upper_limit_inclusive_or_none, rate)
OLD_REGIME_SLABS: List[Tuple[float, float | None, float]] = [
    (0, 250000, 0.0),
    (250000, 500000, 0.05),
    (500000, 1000000, 0.20),
    (1000000, None, 0.30),
]

NEW_REGIME_SLABS: List[Tuple[float, float | None, float]] = [
    (0, 400000, 0.0),
    (400000, 800000, 0.05),
    (800000, 1200000, 0.10),
    (1200000, 1600000, 0.15),
    (1600000, 2000000, 0.20),
    (2000000, 2400000, 0.25),
    (2400000, None, 0.30),
]

STANDARD_DEDUCTION = {
    "old": 50000,
    "new": 75000,
}

REBATE_87A = {
    "old": {"income_limit": 500000, "max_rebate": 12500},
    "new": {"income_limit": 1200000, "max_rebate": 60000},
}

CESS_RATE = 0.04

DEDUCTION_LIMITS: Dict[str, Dict[str, float | str]] = {
    "80C": {
        "limit": 150000,
        "category": "Investment",
        "description": "PPF, EPF, ELSS, life insurance, tuition fees, NSC, home loan principal, etc.",
    },
    "80CCD(1B)": {
        "limit": 50000,
        "category": "Investment",
        "description": "Additional NPS deduction over and above Section 80C.",
    },
    "80D": {
        "limit": 100000,
        "category": "Health",
        "description": "Health insurance premium for self/family and parents based on age.",
    },
    "80E": {
        "limit": 99999999,
        "category": "Education",
        "description": "Education loan interest paid, available for up to 8 years.",
    },
    "80G": {
        "limit": 99999999,
        "category": "Donations",
        "description": "Eligible donations, 50% or 100% depending on institution.",
    },
    "80TTA": {
        "limit": 10000,
        "category": "Other",
        "description": "Savings account interest deduction for non-senior citizens.",
    },
    "80TTB": {
        "limit": 50000,
        "category": "Other",
        "description": "Interest deduction for senior citizens.",
    },
    "24(b)": {
        "limit": 200000,
        "category": "Housing",
        "description": "Home loan interest on self-occupied property.",
    },
    "HRA": {
        "limit": 99999999,
        "category": "Housing",
        "description": "House Rent Allowance exemption under old regime.",
    },
    "LTA": {
        "limit": 99999999,
        "category": "Other",
        "description": "Leave Travel Allowance, subject to journey proof rules.",
    },
}

SECTION_CATEGORIES = ["Investment", "Health", "Housing", "Education", "Donations", "Other"]

CONFIDENCE_LABELS = {
    "high": "🟢 High",
    "medium": "🟡 Medium",
    "low": "🔴 Needs CA Review",
}

STATUS_LABELS = {
    "verified": "✅ Verified",
    "needs_document": "⚠️ Needs Document",
    "conflicting": "❌ Conflicting",
}

SAMPLE_PROFILE = {
    "name": "Rahul",
    "city": "Chennai",
    "city_type": "metro",
    "age": 29,
    "annual_income": 1200000,
    "basic_salary": 600000,
    "hra_received": 120000,
    "rent_paid": 240000,
    "investments": {
        "80C": 80000,
        "80D": 25000,
        "ELSS": 30000,
        "PPF": 50000,
        "80CCD(1B)": 0,
    },
    "declared_deductions": {
        "80C": 80000,
        "80D": 25000,
    },
    "savings_interest": 8000,
    "education_loan_interest": 0,
    "donations": 0,
    "home_loan_interest": 0,
}

SAMPLE_DOCUMENT_TEXT = """
Employee Name: Rahul Sharma
Employer: Chennai Tech Labs Pvt Ltd
Annual CTC: ₹12,00,000
Basic Salary: ₹6,00,000
House Rent Allowance (HRA): ₹1,20,000
Rent Paid: ₹2,40,000
PPF Contribution: ₹50,000
ELSS Investment: ₹30,000
Health Insurance Premium: ₹25,000
Savings Account Interest: ₹8,000
""".strip()

UI_COLORS = {
    "primary": "#0F52BA",
    "success": "#1E8E3E",
    "warning": "#F9AB00",
    "danger": "#D93025",
    "neutral": "#5F6368",
}

MAX_AGENT_STEPS = 3


def format_inr(amount: float | int) -> str:
    """Format number in Indian currency style."""
    amount = float(amount or 0)
    sign = "-" if amount < 0 else ""
    amount = abs(amount)
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))
    s = str(rupees)
    if len(s) > 3:
        head = s[:-3]
        tail = s[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        s = ",".join(groups + [tail])
    return f"{sign}{CURRENCY_SYMBOL}{s}.{paise:02d}"