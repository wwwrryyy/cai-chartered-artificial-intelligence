# CAI: Chartered AI (Kaggle Edition)

**Autonomous Tax Intelligence powered by Gemma 3**

## 📌 Problem Statement
India’s tax filing process remains highly complex for salaried employees and freelancers. While traditional tax calculators exist, they require tedious manual data entry and lack proactive intelligence. Taxpayers often miss out on valid deductions, struggle to decide between the Old and New Tax Regimes, and face anxiety over potential compliance errors. 

**CAI (Chartered AI)** bridges this gap. It acts as an autonomous financial agent that visually reads Form 16s and investment proofs, automatically discovers missing deductions, and provides a clear, mathematical comparison between tax regimes—all wrapped in a stunning, consumer-grade interface.

---

## 🏗️ Product Architecture

CAI has evolved from a basic prototype into a decoupled, modern web application architecture designed for speed, privacy, and visual excellence.

### 1. The Intelligence Layer (AI & Vision)
- **Model:** `gemma3:4b` (running locally via Ollama) or `gemini-1.5-pro` (via Cloud API) for deep visual understanding.
- **Vision Extraction:** CAI natively processes document images (like Form 16 PNGs) using Gemma's multimodal capabilities, converting complex financial tables into a structured JSON schema.
- **Deduction Discovery Engine:** Analyzes the extracted profile against Indian tax sections (80C, 80D, 80CCD(1B), etc.) to flag eligible, claimed, and missed opportunities.

### 2. The Backend Layer (FastAPI)
- **Framework:** Python / FastAPI
- **Tax Engine:** A deterministic, hard-coded tax calculator updated for the latest Budget 2026-27 (e.g., ₹12 Lakh 87A rebate limit in the New Regime). 
- **State Management:** In-memory session tracking ensures that file lists and deduction states remain persistent across API calls without needing a heavy database.

### 3. The Frontend Layer (React + Vite)
- **Framework:** React 18 powered by Vite.
- **Design System:** Custom CSS (`index.css`) featuring deep dark modes, frosted "iOS Liquid Glass" morphisms, and dynamic micro-animations (like the mechanical `OptionWheel` and floating 3D ASCII art canvas).
- **Three.js Integration:** A custom background renderer that maps the "CAI" brand onto an animated, mathematical sine-wave grid.

---

## 🚀 Key Innovations

1. **Multimodal Form 16 Parsing:** Users simply drag and drop their tax forms. Gemma handles the OCR, semantic understanding, and structured extraction in one pass.
2. **Deterministic Fallbacks:** While Gemma handles the reasoning and extraction, the actual tax math (slabs, cess, rebates) is routed to a deterministic Python engine. This guarantees mathematical correctness while retaining AI flexibility.
3. **Immersive UI/UX:** Tax software is notoriously boring. CAI flips this by offering an immersive, premium interface with 3D canvas backgrounds, audio-feedback navigation dials, and glassmorphism cards.
4. **Local-First Privacy:** By supporting `gemma3:4b` via Ollama, sensitive financial documents can be processed entirely offline, guaranteeing absolute privacy for the taxpayer.

---

## ⚙️ How to Run Locally

### Prerequisites
- Node.js & npm (for frontend)
- Python 3.10+ (for backend)
- Ollama with `gemma3:4b` installed (for local AI)

### 1. Start the Backend
```bash
cd cai-backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Start the Frontend
```bash
cd cai
npm install
npm run dev
```

### 3. Usage
Navigate to `http://localhost:5173`. Drop a Form 16 into the Upload tab, and watch CAI extract your salary, parse your investments, and build your personalized tax strategy.
