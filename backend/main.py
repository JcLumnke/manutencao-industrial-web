import os
import json
import logging
import traceback
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
    # Print library version for SquareCloud logs (best-effort)
    genai_version = None
    try:
        genai_version = getattr(genai, "__version__", None)
    except Exception:
        genai_version = None
    if not genai_version:
        try:
            import importlib.metadata as importlib_metadata
            genai_version = importlib_metadata.version("google-generativeai")
        except Exception:
            genai_version = "unknown"
    print(f"GENAI LIB: google-generativeai version={genai_version}")
    print(f"GAPIC LIB: {'present' if gapic is not None else 'missing'}")

    # Prefer configuring api_base to v1 if the configure function accepts it.
    try:
        try:
            genai.configure(api_key=os.environ["GEMINI_API_KEY"], api_base="https://generative.googleapis.com/v1")
            print("genai.configure called with api_base=https://generative.googleapis.com/v1")
        except TypeError:
            # Older/newer versions may not accept api_base kwarg
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            print("genai.configure called (no api_base kwarg)")
    except KeyError as e:
        logging.error("GEMINI_API_KEY missing: %s", e)
        print(str(e))
    except Exception as e:
        logging.exception("genai.configure failed: %s", str(e))
        print(f"genai.configure failed: {e}")

    # Best-effort: set common attributes that may force v1 endpoints
    for attr, val in (("api_version", "v1"), ("api_base", "https://generative.googleapis.com/v1")):
        try:
            if hasattr(genai, attr):
                setattr(genai, attr, val)
                print(f"Set genai.{attr} = {val}")
        except Exception:
            pass


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
    equipment_name: Optional[str] = "Não informado"  # NOVO CAMPO ADICIONADO
    machine_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DiagnoseResponse(BaseModel):
    diagnosis: Dict[str, Any]
    raw_output: str


def build_prompt(req: DiagnoseRequest) -> str:

    parts = [
        f"EQUIPAMENTO: {req.equipment_name}",
        "Você é um engenheiro de manutenção industrial experiente. Dados os sintomas abaixo, gere um único objeto JSON com os campos exatos:",
        "- summary: resumo conciso do problema",
        "- probable_causes: lista de objetos {cause: string, likelihood: number 0-100}",
        "- severity: um de low|medium|high|critical",
        "- recommended_actions: lista ordenada de passos",
        "- troubleshooting_steps: lista passo-a-passo para diagnóstico",
        "- estimated_parts: lista de peças/códigos necessários",
        "- estimated_time_hours: número aproximado de horas",
        "- confidence: número entre 0 e 1",
        "- required_tools: lista de ferramentas",
        "- recommended_tests: lista de testes a realizar",
        "- logs_needed: lista de logs/medições para coletar",
        "- component: componente provável (ex: motor, bomba, PLC, sensor)",
        "- category: mechanical|electrical|software|sensor",
        "- maintenance_priority: inteiro 1-5",
        "Retorne APENAS o JSON (sem texto explicativo adicional).",
        "SYMPTOMS:",
        req.symptoms,
    ]
    if req.machine_id:
        parts.insert(1, f"Machine ID: {req.machine_id}")
    if req.metadata:
        parts.append("METADATA:")
        parts.append(json.dumps(req.metadata, ensure_ascii=False))
    return "\n".join(parts)


def _extract_text_from_resp(resp: Any) -> str:
    try:
        if isinstance(resp, dict):
            if "candidates" in resp and resp["candidates"]:
                c = resp["candidates"][0]
                if isinstance(c, dict):
                    return c.get("content") or c.get("text") or c.get("output") or str(c)
                return str(c)
    except Exception:
        pass
    try:
        if hasattr(resp, "candidates"):
            cand = getattr(resp, "candidates")
            if cand:
                first = cand[0]
                if hasattr(first, "content"):
                    return first.content
                if hasattr(first, "text"):
                    return first.text
    except Exception:
        pass
    return str(resp)


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
    if os.getenv("GEMINI_TEST_MODE") == "1":
        sample = {"summary": "Modo teste ativo", "confidence": 0.99}
        raw = json.dumps(sample, ensure_ascii=False)
    else:
        try:
            if genai is None:
                raise RuntimeError("Biblioteca GenAI não disponível.")
            
            raw = None
            last_exc = None
            for model_name in ("gemini-2.0-flash", "gemini-flash-latest"):
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    text = getattr(response, "text", None)
                    if not text:
                        text = _extract_text_from_resp(response)
                    raw = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False)
                    print(f"Used model: {model_name}")
                    break
                except Exception as e:
                    print(f"ERRO REAL (model={model_name}): {e}")
                    last_exc = e
            
            if raw is None:
                if last_exc:
                    raise HTTPException(status_code=500, detail=f"ERRO: {str(last_exc)}")
        except Exception as e:
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"ERRO: {str(e)}")

    try:
        parsed = extract_json_from_text(raw)
    except ValueError:
        parsed = {"error": "Falha no parse do JSON", "raw": raw}
    return {"diagnosis": parsed, "raw_output": raw}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")