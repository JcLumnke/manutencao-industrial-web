import os
import json
import logging
import traceback
import time
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)

# Use only google.generativeai as requested
try:
    import google.generativeai as genai
except Exception:
    genai = None

# Optionally import GAPIC v1 client to force stable v1 behavior
try:
    from google.ai import generativelanguage_v1 as gapic
except Exception:
    gapic = None

# Try to configure genai and prefer the stable v1 API when possible.
if genai is not None:
    try:
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"], api_base="https://generative.googleapis.com/v1")
        except TypeError:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except Exception as e:
        logging.exception("genai.configure failed: %s", str(e))

app = FastAPI(title="Motor de Diagnóstico - Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiagnoseRequest(BaseModel):
    symptoms: str = Field(..., description="Descrição dos sintomas")
    equipment_name: Optional[str] = "Não informado"
    machine_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DiagnoseResponse(BaseModel):
    diagnosis: Dict[str, Any]
    raw_output: str

def build_prompt(req: DiagnoseRequest) -> str:
    query_id = int(time.time())
    
    parts = [
        f"### ID DA CONSULTA: {query_id} ###",
        f"EQUIPAMENTO: {req.equipment_name}",
        "CONTEXTO: Engenheiro de Manutenção Sênior. FOCO: Diagnóstico técnico rápido e preciso.",
        "IDIOMA: RESPONDA EXCLUSIVAMENTE EM PORTUGUÊS DO BRASIL.",
        
        "REGRAS DE RESPOSTA:",
        "1. No campo 'summary', forneça o diagnostic técnico em 3 a 5 tópicos (bullet points) diretos.",
        "2. Use terminologia técnica profissional (ex: cavitação, folga, surto de tensão).",
        "3. Escreva tudo em PORTUGUÊS. Não use inglês nos valores do JSON.",
        
        "GERE UM ÚNICO OBJETO JSON COM ESTES CAMPOS EXATOS:",
        "- summary: Diagnóstico técnico conciso em tópicos.",
        "- probable_causes: lista de {cause: string, likelihood: 0-100}",
        "- severity: low|medium|high|critical",
        "- recommended_actions: passos técnicos de reparo.",
        "- troubleshooting_steps: sequência lógica para isolar a falha.",
        "- estimated_parts: peças e ferramentas necessárias.",
        "- estimated_time_hours: tempo aproximado.",
        "- confidence: número de 0 a 1.",
        "- component: componente afetado (ex: motor, CLP, bomba).",
        "- category: mechanical|electrical|software|sensor",
        "- maintenance_priority: 1 a 5.",
        
        "RETORNE APENAS O JSON. SEM TEXTO ADICIONAL.",
        "SINTOMAS ATUAIS:",
        req.symptoms,
    ]
    
    if req.machine_id:
        parts.insert(1, f"ID DA MÁQUINA: {req.machine_id}")
    if req.metadata:
        parts.append("METADADOS DE TELEMETRIA:")
        parts.append(json.dumps(req.metadata, ensure_ascii=False))
        
    return "\n".join(parts)

def _extract_text_from_resp(resp: Any) -> str:
    try:
        if isinstance(resp, dict):
            if "candidates" in resp and resp["candidates"]:
                c = resp["candidates"][0]
                return c.get("content") or c.get("text") or str(c)
    except Exception: pass
    try:
        if hasattr(resp, "candidates") and resp.candidates:
            first = resp.candidates[0]
            if hasattr(first, "content"): return first.content
            if hasattr(first, "text"): return first.text
    except Exception: pass
    return str(resp)

def extract_json_from_text(text: str):
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try: return json.loads(text[start:end+1])
            except Exception: pass
    raise ValueError("Não foi possível extrair JSON.")

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    prompt = build_prompt(req)
    
    generation_config = {
        "temperature": 0.2,     
        "top_p": 0.8,            
        "top_k": 40,            
        "max_output_tokens": 1024 
    }

    if os.getenv("GEMINI_TEST_MODE") == "1":
        return {"diagnosis": {"summary": "Modo teste"}, "raw_output": "{}"}
    
    try:
        raw = None
        last_exc = None
        for model_name in ("gemini-2.0-flash", "gemini-flash-latest"):
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    generation_config=generation_config
                )
                response = model.generate_content(prompt)
                text = getattr(response, "text", None) or _extract_text_from_resp(response)
                raw = text if isinstance(text, str) else json.dumps(text)
                break
            except Exception as e:
                last_exc = e
        
        if raw is None: raise last_exc
        parsed = extract_json_from_text(raw)
        return {"diagnosis": parsed, "raw_output": raw}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")