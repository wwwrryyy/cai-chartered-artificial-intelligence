# CAI: Autonomous Tax Filing Agent Powered by Gemma 4

## Subtitle
**Finding every deduction, missing nothing — AI that works like a Chartered Accountant**

## Track
**Agents on a Mission**

---

## Problem Statement
India’s income tax filing experience is still difficult for a large segment of salaried and self-managed taxpayers, especially first-time filers. Most users know they should “save tax,” but they do not know which sections apply to them, which proofs are mandatory, or whether the old regime or new regime is better. As a result, people either overpay tax or make risky claims without proper evidence. Existing tools are usually static calculators: they ask users to fill many fields manually and provide no proactive guidance. This creates friction, confusion, and anxiety during filing season.

CAI addresses this gap by acting like a practical tax reasoning agent rather than a plain form. It accepts uploaded documents and free-text financial descriptions, identifies relevant deductions under Indian sections (80C, 80D, HRA, 80E, 80G, etc.), checks missing proofs, computes tax under both regimes, and explains recommendations in clear Indian English. The goal is simple: help users find legitimate savings, avoid compliance mistakes, and make tax decisions with confidence.

## Solution Overview
CAI is a Streamlit-based intelligent assistant designed for Indian taxpayers and built around Gemma 4 as the core reasoning engine. The app combines document understanding, conversational parsing, tool-driven tax computation, and explainability into one workflow optimised for a hackathon demo and real user value.

The user can start in two ways: upload tax-related documents (salary slip, rent proof, insurance premium receipt, etc.) or directly type their financial details in plain language. Gemma converts these inputs into a structured profile with income, HRA, investment declarations, and relevant claim candidates. Then the deduction discovery engine proactively scans opportunities and highlights what is verified, what is probable, and what needs proof.

Next, the computation layer evaluates both old and new regimes, applies rules such as standard deduction and Section 87A rebate, and provides final tax comparison with effective rates. A scenario planner then suggests actionable what-if options (for example, additional ELSS or NPS contribution) and estimates tax impact. Finally, an audit risk module flags suspicious ratios or missing evidence and recommends safer filing practices.

The app includes report export (Markdown/PDF), session memory across tabs, and an agent trace panel showing which tools were called during reasoning. This design transforms a confusing tax process into a transparent, guided, and decision-centric experience.

## Gemma 4 Integration
Gemma 4 is central to CAI’s architecture, not a side chatbot. We use Gemma in five major reasoning pathways:

1. **Structured extraction from raw content**: Uploaded PDF/image text and user free-text are transformed into structured financial JSON. This removes manual form fatigue and supports natural user behaviour.
2. **Proactive deduction discovery**: Gemma evaluates financial context against Indian sections and identifies qualified, partially qualified, and potential claims.
3. **Tool-planning agent behaviour**: Gemma decides which analytical tools to call (slab lookup, deduction checks, tax compute, claim verification), enabling an agent-like loop instead of static prompts.
4. **Scenario generation**: Gemma proposes practical “what-if” tax planning actions with estimated savings and confidence.
5. **Natural-language summarisation**: Gemma produces understandable final recommendations and next-step checklists.

### Agent Loop (Plan → Execute → Verify)
CAI follows a lightweight function-calling pattern:
- **Plan**: Gemma receives user context + tool schema and returns selected tool calls.
- **Execute**: Local Python tools run deterministic checks and tax computations.
- **Verify/Synthesise**: Gemma converts tool outputs into explainable guidance.

This architecture balances generative intelligence with deterministic financial correctness.

### Confidence Tiers
Every recommendation is classified with confidence badges:
- **High**: Verified from document evidence
- **Medium**: Declared by user, plausible but unverified
- **Needs CA Review**: Complex/uncertain/conflicting

This prevents overconfident AI behaviour and improves trust.

## Architecture
CAI follows a modular 10+ file architecture built for maintainability and quick demo stability:

- **app.py**: Streamlit UI, tabs, user interactions, spinners, error handling.
- **gemma_client.py**: Central Gemma wrapper for extraction, deduction discovery, scenarios, risk analysis, summaries.
- **tax_engine.py**: Deterministic Indian tax rules (slabs, standard deduction, rebate, cess, regime comparison).
- **document_parser.py**: PDF/image extraction pipeline using pdfplumber/PyPDF2/Pillow/pytesseract.
- **agent_core.py**: Plan-execute-respond orchestration with trace logs.
- **tools.py**: Tool schema + execution dispatcher for slab lookup, eligibility checks, tax compute, and claim verification.
- **memory.py**: Session state persistence across tabs.
- **report_generator.py**: Markdown + PDF export for full advisory report.
- **config.py**: Slabs, limits, constants, categories, sample demo profile.
- **prompts.py**: Structured prompt templates enforcing JSON outputs and non-fabrication.

### Why this architecture works in a 1-day sprint
- Clear separation between **reasoning** (Gemma) and **calculation** (tax engine)
- Easy to debug due to explicit module ownership
- Fast UI iteration because core logic is reusable and isolated
- Demo reliability from local fallbacks + deterministic tool layer

## Key Innovations
1. **Proactive Deduction Discovery Engine**
   Instead of asking “what do you want to claim?”, CAI scans eligibility space and identifies missed opportunities (e.g., remaining 80C room, extra 80CCD(1B) option).

2. **Missing Evidence Detector**
   CAI cross-checks claimed items versus available documents and marks each item as verified, needs document, or conflicting.

3. **Confidence-Tiered Recommendations**
   Users instantly understand reliability of each suggestion, reducing unsafe filing behaviour.

4. **What-If Scenario Planner**
   Converts tax advice into actionable choices with measurable impact (invest x, save y).

5. **Audit Risk Flagging**
   Highlights practical compliance risks (high deduction ratios, evidence gaps, mismatch patterns) with mitigation steps.

6. **Explainability-by-default**
   Every deduction card includes “Why this?” reasoning trace so users and judges can audit AI logic.

7. **Transparent Agent Trace**
   Tool calls are exposed in UI, proving that the system performs structured reasoning and not black-box guessing.

## Challenges in 1-Day Sprint
The biggest challenge was balancing generative flexibility with financial correctness under hackathon time constraints. Tax advice can’t rely only on language model text; it needs deterministic math, limits, and clear assumptions. We solved this by separating modules: Gemma handles understanding and reasoning, while a local tax engine computes slabs, rebates, cess, and totals.

Another challenge was ensuring demo robustness when input quality varies (unclear documents, mixed statements, partial data). We added validation layers, user-editable structured profile cards, confidence tags, and evidence gap highlighting. This keeps flow smooth even with imperfect data.

Finally, function-calling compatibility can differ across SDK versions, so we designed a resilient tool-planning approach that remains transparent and traceable for judges.

## Impact & Future Scope
CAI can significantly improve financial inclusion by giving first-time and non-expert taxpayers CA-style guidance in simple language. It reduces overpayment risk, clarifies filing readiness, and nudges users toward compliant behaviour.

Future scope:
- Multi-language support (Tamil, Hindi, Telugu, Kannada) for wider accessibility
- Integration with Form 16, AIS, and 26AS parsers
- Secure connector workflows for Indian filing portals
- Smart notifications for tax-saving deadlines
- Deeper handling for freelancers/business income and presumptive taxation
- OCR quality scoring and document authenticity checks

In short, CAI can evolve from a hackathon prototype into a practical personal tax copilot for millions of Indian taxpayers.

## Demo Highlights
In a 2-minute flow, CAI shows end-to-end autonomy: sample data load, deduction discovery, old-vs-new tax comparison, scenario-based savings, audit risk score, downloadable report, and visible agent trace. Judges can see Gemma reasoning at every stage, not just as a chatbot overlay. The result is a transparent, actionable, and India-specific tax intelligence experience ready for real-world extension.