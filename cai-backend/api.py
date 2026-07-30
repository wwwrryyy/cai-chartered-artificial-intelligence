from typing import List

import uvicorn
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

from document_parser import parse_pdf, parse_image, extract_financial_fields
from tax_engine import compare_regimes
from gemma_client import discover_deductions, _default_profile

app = FastAPI(title="CAI Backend API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for simple single-user state
app_state = {
    "profile": _default_profile(),
    "tax_result": {},
    "deductions": [],
    "files": []
}

@app.post("/api/reset")
def reset_state():
    global app_state
    app_state = {
        "profile": _default_profile(),
        "tax_result": {},
        "deductions": [],
        "files": []
    }
    return {"status": "success", "message": "State reset"}

@app.get("/api/dashboard")
def get_dashboard():
    profile = app_state["profile"]
    
    # Calculate tax based on current profile if income > 0
    if profile.get("annual_income", 0) > 0:
        deductions_map = {d.get("section", "Other"): d.get("eligible_amount", 0.0) for d in app_state["deductions"]}
        app_state["tax_result"] = compare_regimes(profile.get("annual_income", 0.0), deductions_map)
    
    tax = app_state["tax_result"]
    total_income = profile.get("annual_income", 0)
    
    # Extract final tax based on recommended regime
    recommended = tax.get("recommended_regime", "old")
    final_tax = 0
    if recommended == "old" and "old_regime" in tax:
        final_tax = tax["old_regime"].get("final_tax", 0)
    elif recommended == "new" and "new_regime" in tax:
        final_tax = tax["new_regime"].get("final_tax", 0)
        
    deductions_found = sum(d.get("eligible_amount", 0) for d in app_state["deductions"])
    
    return {
        "total_income": total_income,
        "tax_liability": final_tax,
        "deductions_found": deductions_found,
        "profile": profile,
        "tax_result": tax,
        "deductions": app_state["deductions"],
        "files": app_state["files"]
    }

@app.post("/api/upload")
async def upload_document(files: List[UploadFile] = File(...)):
    import base64
    all_text = []
    images = []
    for file in files:
        contents = await file.read()
        app_state["files"].append(file.filename)
        if file.filename.lower().endswith(".pdf") or file.filename.endswith(".txt"):
            text = parse_pdf(contents) if file.filename.lower().endswith(".pdf") else contents.decode('utf-8', errors='ignore')
            all_text.append(f"--- {file.filename} ---\n{text}")
        else:
            b64_img = base64.b64encode(contents).decode("utf-8")
            images.append(b64_img)
            all_text.append(f"--- {file.filename} ---\n[Image Attached]")
    
    combined_text = "\n\n".join(all_text)
    
    # Extract structural profile
    extracted_profile = extract_financial_fields(combined_text, images=images)
    
    # Merge extracted profile into app state
    for k, v in extracted_profile.items():
        if k in ["investments", "declared_deductions"]:
            if k not in app_state["profile"]:
                app_state["profile"][k] = {}
            if isinstance(v, dict):
                for inner_k, inner_v in v.items():
                    app_state["profile"][k][inner_k] = inner_v
        else:
            app_state["profile"][k] = v
            
    # Also discover deductions
    deductions_result = discover_deductions(app_state["profile"])
    deductions = deductions_result.get("deductions", [])
    app_state["deductions"] = deductions
    
    return {
        "status": "success", 
        "extracted": extracted_profile, 
        "deductions_count": len(deductions)
    }

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
