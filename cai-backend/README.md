# CAI

Autonomous Indian tax planning assistant powered by **Gemma 4** with document intelligence, deduction discovery, and old-vs-new regime optimisation.

## Prerequisites

- Python **3.10+** (recommended: 3.12 if package compatibility issues appear on 3.14)
- Tesseract OCR installed (required for PNG/JPG text extraction)
- Gemma API key (`GEMMA_API_KEY`)

### Install Tesseract

**Ubuntu/Debian**
```bash
sudo apt-get update
sudo apt-get install -y tesseract-ocr
```

**macOS (Homebrew)**
```bash
brew install tesseract
```

**Windows**
- Install from official Tesseract installer and add it to PATH.

## Setup

1. Clone or copy this `cai-ai` directory.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   Update `.env`:
   ```env
   GEMMA_API_KEY=your_actual_key
   GEMMA_MODEL=gemma-4
   ```

## Run

```bash
streamlit run app.py
```

## Demo Mode (2-minute hackathon flow)

1. Enter name as **Rahul** in sidebar.
2. Open **📄 Document Upload** tab and click **Load Sample Data**.
3. Click **Confirm Extraction**.
4. Open **🔍 Discover Deductions** tab.
5. Click **Find All Deductions**.
6. Click **Compute Tax**.
7. Open **📊 Tax Summary & Report** tab.
8. Click **Generate Scenarios** and then **Download PDF Report**.
9. Expand **🧠 Agent Trace** to show tool calls.

## Gemma Integration Highlights

- Structured extraction from documents and plain-language input
- Proactive deduction discovery across Indian tax sections
- Tool-based reasoning loop with traceable decisions
- Scenario planning and audit risk assessment
- Explainable recommendations with confidence tiers

## Team Credits

Built by a 4-member first-year CS student team (VIT Chennai) for **Build with Gemma (Gemma 4)**.

---

If package install fails on Python 3.14 due wheel availability, use:
```bash
pip install --pre -r requirements.txt
```
or switch to Python 3.12 for stable binary compatibility.