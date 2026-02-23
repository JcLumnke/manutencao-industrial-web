import os
import json
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

try:
    from google import generativeai as genai
except Exception:
    try:
        import google.generativeai as genai
    except Exception:
        genai = None

API_KEY = os.getenv("GEMINI_API_KEY")
if genai and API_KEY:
    try:
        if hasattr(genai, "configure"):
            genai.configure(api_key=API_KEY)
        elif hasattr(genai, "client") and hasattr(genai.client, "configure"):
            genai.client.configure(api_key=API_KEY)
    except Exception:
        logging.exception("Falha ao configurar Gemini client")

app = FastAPI(title="Motor de Diagnóstico - Backend")

# CORS configuration: allow Vercel preview domains and local development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class DiagnoseRequest(BaseModel):
    symptoms: str = Field(..., description="Descrição dos sintomas")
    machine_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DiagnoseResponse(BaseModel):
    diagnosis: Dict[str, Any]
    raw_output: str

def build_prompt(req: DiagnoseRequest) -> str:
    parts = []
    if req.machine_id:
        parts.append(f"Machine ID: {req.machine_id}")
    parts.append("Você é um engenheiro de manutenção industrial experiente. Dados os sintomas abaixo, gere um único objeto JSON com os campos exatos:")
    parts.append("- summary: resumo conciso do problema")
    parts.append("- probable_causes: lista de objetos {cause: string, likelihood: number 0-100}")
    parts.append("- severity: um de low|medium|high|critical")
    parts.append("- recommended_actions: lista ordenada de passos")
    parts.append("- troubleshooting_steps: lista passo-a-passo para diagnóstico")
    parts.append("- estimated_parts: lista de peças/códigos necessários")
    parts.append("- estimated_time_hours: número aproximado de horas")
    parts.append("- confidence: número entre 0 e 1")
    parts.append("- required_tools: lista de ferramentas")
    parts.append("- recommended_tests: lista de testes a realizar")
    parts.append("- logs_needed: lista de logs/medições para coletar")
    parts.append("- component: componente provável (ex: motor, bomba, PLC, sensor)")
    parts.append("- category: mechanical|electrical|software|sensor")
    parts.append("- maintenance_priority: inteiro 1-5")
    parts.append("Retorne APENAS o JSON (sem texto explicativo adicional).")
    parts.append("SYMPTOMS:")
    parts.append(req.symptoms)
    if req.metadata:
        parts.append("METADATA:")
        parts.append(json.dumps(req.metadata, ensure_ascii=False))
    return "\n".join(parts)

def call_gemini(prompt: str) -> str:
    # Modo de teste local: quando GEMINI_TEST_MODE=1 retorna resposta simulada
    if os.getenv("GEMINI_TEST_MODE") == "1":
        sample = {
            "summary": "Vibração excessiva no eixo e aumento de temperatura do motor",
            "probable_causes": [
                {"cause": "desbalanceamento do rotor", "likelihood": 70},
                {"cause": "rolamento desgastado", "likelihood": 60}
            ],
            "severity": "high",
            "recommended_actions": [
                "Parar máquina e inspecionar rolamentos",
                "Verificar alinhamento do eixo",
                "Substituir peças danificadas"
            ],
            "troubleshooting_steps": [
                "Medir vibração com vibrômetro",
                "Inspeção visual do rotor",
                "Verificar corrente e tensão do motor"
            ],
            "estimated_parts": ["Rolamento - P/N 1234", "Junta - P/N 5678"],
            "estimated_time_hours": 3.5,
            "confidence": 0.85,
            "required_tools": ["Chave dinamométrica", "Vibrômetro", "Termômetro infravermelho"],
            "recommended_tests": ["Teste de vibração (ISO 10816)", "Medição de temperatura em 3 pontos"],
            "logs_needed": ["Últimos 24h de corrente do motor", "Logs de manutenção últimos 6 meses"],
            "component": "motor",
            "category": "mechanical",
            "maintenance_priority": 2
        }
        return json.dumps(sample, ensure_ascii=False)

    if genai is None:
        raise RuntimeError("Biblioteca 'google-generativeai' não está instalada.")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("Variável de ambiente GEMINI_API_KEY não definida.")
    try:
        if hasattr(genai, "configure"):
            genai.configure(api_key=key)
        elif hasattr(genai, "client") and hasattr(genai.client, "configure"):
            genai.client.configure(api_key=key)
    except Exception:
        pass
    model = os.getenv("GEMINI_MODEL", "gpt-4o-mini")
    try:
        if hasattr(genai, "chat") and hasattr(genai.chat, "completions"):
            resp = genai.chat.completions.create(model=model, messages=[{"role":"user","content":prompt}])
            if isinstance(resp, dict):
                if "candidates" in resp and resp["candidates"]:
                    return resp["candidates"][0].get("content") or resp["candidates"][0].get("text", "")
                if "choices" in resp and resp["choices"]:
                    ch = resp["choices"][0]
                    if isinstance(ch, dict):
                        if "message" in ch and isinstance(ch["message"], dict):
                            return ch["message"].get("content", "")
                        return ch.get("content", "")
            try:
                if hasattr(resp, "choices") and resp.choices:
                    first = resp.choices[0]
                    try:
                        return first.message.content
                    except Exception:
                        return getattr(first, "output_text", "")
            except Exception:
                pass
        if hasattr(genai, "text") and hasattr(genai.text, "generate"):
            resp = genai.text.generate(model=model, prompt=prompt)
            if isinstance(resp, dict):
                if "candidates" in resp and resp["candidates"]:
                    return resp["candidates"][0].get("content") or resp["candidates"][0].get("text", "")
                if "output" in resp:
                    return resp["output"]
            gens = getattr(resp, "generations", None)
            if gens:
                first = gens[0]
                if isinstance(first, dict):
                    return first.get("text") or first.get("content", "")
                else:
                    return getattr(first, "text", "")
        if hasattr(genai, "generate_text"):
            resp = genai.generate_text(model=model, prompt=prompt)
            if isinstance(resp, dict) and "candidates" in resp:
                return resp["candidates"][0].get("output") or resp["candidates"][0].get("content", "")
            return getattr(resp, "output_text", str(resp))
    except Exception as e:
        raise RuntimeError(f"Erro ao chamar API Gemini: {e}")
    raise RuntimeError("Resposta inesperada da API Gemini.")

def extract_json_from_text(text: str):
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            try:
                return json.loads(candidate)
            except Exception:
                pass
    raise ValueError("Não foi possível extrair JSON da resposta do modelo.")

@app.get("/")
async def root():
    return {"status": "ok"}

@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    prompt = build_prompt(req)
    try:
        raw = call_gemini(prompt)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    try:
        parsed = extract_json_from_text(raw)
    except ValueError:
        parsed = {"error": "Não foi possível parsear JSON da resposta do modelo.", "raw": raw}
    return {"diagnosis": parsed, "raw_output": raw}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")
