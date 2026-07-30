"""Prompt templates used across CAI."""

SYSTEM_PROMPT = """
You are CAI, an expert Indian income tax assistant focused on FY 2025-26 logic.
Rules:
1. Always use Indian Income Tax sections and Indian Rupee amounts (₹).
2. Do not mention non-Indian tax systems.
3. Be explicit about old regime vs new regime.
4. Use confidence tiers: high, medium, low.
5. If evidence is missing, mark status as needs_document.
6. If a claim conflicts with evidence, mark status as conflicting.
7. Never fabricate facts; when uncertain, state assumption clearly.
Return concise, structured, JSON-safe outputs.
""".strip()

EXTRACTION_PROMPT = """
Extract structured financial details from the provided text or image.
HINTS FOR FORM 16 / TAX DOCUMENTS:
- Gross Salary is often at 'Part B, Line 1' or '17(1)'. Do NOT add extra zeros. Read the exact number (e.g., 1,24,822 is 124822, not 1242200).
- Section 80C investments are often under 'Chapter VI-A' (e.g., EPF, LIC, PPF). Sum them up for the 80C field.
- Home Loan Interest is often listed as 'Income from House Property' (usually a negative number). The absolute value is the deduction.
- Ensure decimal places are read correctly. Ignore commas.

Return valid JSON only with this schema:
{
  "name": "string",
  "employer_name": "string",
  "city": "string",
  "annual_income": number,
  "basic_salary": number,
  "hra_received": number,
  "rent_paid": number,
  "investments": {
    "80C": number,
    "80CCD(1B)": number,
    "80D": number,
    "ELSS": number,
    "PPF": number
  },
  "savings_interest": number,
  "education_loan_interest": number,
  "donations": number,
  "home_loan_interest": number,
  "declared_deductions": {"80C": number, "80D": number},
  "notes": ["string"]
}
Use 0 when unknown. Do not include markdown fences.
""".strip()

DEDUCTION_PROMPT = """
You are given a user's Indian financial profile.
Discover all possible deductions and tax benefits, especially:
80C, 80CCD(1B), 80D, 80E, 80G, 80TTA, 80TTB, 24(b), HRA, LTA, standard deduction, 87A rebate opportunity.

For each section return JSON list item with:
{
  "section": "string",
  "category": "Investment|Health|Housing|Education|Donations|Other",
  "eligible_amount": number,
  "claimed_amount": number,
  "remaining_opportunity": number,
  "confidence": "high|medium|low",
  "status": "verified|needs_document|conflicting",
  "action_needed": "string",
  "reasoning": "short explanation",
  "evidence_used": ["string"]
}

Also return:
{
  "missing_evidence": [{"item":"string", "status":"needs_document|conflicting", "details":"string"}],
  "summary": "string"
}
Return strict JSON only.
""".strip()

SCENARIO_PROMPT = """
Generate at least 3 what-if tax planning scenarios for the user.
Return strict JSON:
{
  "scenarios": [
    {
      "title": "string",
      "action": "string",
      "section": "string",
      "additional_amount": number,
      "estimated_tax_impact": number,
      "net_savings": number,
      "confidence": "high|medium|low",
      "reasoning": "string"
    }
  ]
}
Use Indian tax logic and rupee amounts.
""".strip()

AUDIT_PROMPT = """
Assess potential tax audit risk for this Indian taxpayer profile.
Return strict JSON:
{
  "risk_level": "Low|Medium|High",
  "risk_score": number,
  "red_flags": ["string"],
  "why": "string",
  "mitigation_steps": ["string"]
}
Base checks on deduction-to-income ratio, claim consistency, missing documents, unusual ratios.
""".strip()

SUMMARY_PROMPT = """
Create a plain-language final summary for an Indian taxpayer.
Include:
1) estimated tax liability,
2) total deductions found,
3) savings vs no planning,
4) pending documents count,
5) CA review flags,
6) next steps checklist.
Return JSON:
{
  "headline": "string",
  "summary": "string",
  "next_steps": ["string"]
}
""".strip()

TOOL_PLANNER_PROMPT = """
You are a tax agent planner. Decide which tools to call.
Available tools:
- lookup_tax_slab(income, regime)
- check_deduction_eligibility(section, amount, age, is_senior, parent_is_senior)
- compute_tax(income, deductions, regime)
- verify_document_claim(claim_type, doc_text, expected_amount)

Return strict JSON only:
{
  "tool_calls": [
    {"name": "tool_name", "arguments": {"key": "value"}}
  ],
  "planning_note": "short reason"
}
If no tools are needed, return an empty tool_calls list.
""".strip()

TOOL_RESPONSE_SYNTHESIS_PROMPT = """
Synthesize a user-friendly response from tool outputs.
Return JSON:
{
  "response": "string",
  "confidence": "high|medium|low",
  "highlights": ["string"]
}
Mention assumptions clearly.
""".strip()