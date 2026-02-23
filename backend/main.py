import os
import json
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)

# Import genai libraries with sensible fallbacks
genai = None
genai_name = None
try:
    from google import genai as genai  # preferred
    genai_name = "google.genai"
except Exception:
    try:
        import google.genai as genai
        genai_name = "google.genai"
    except Exception:
        try:
            from google import generativeai as genai
            genai_name = "google.generativeai"
        except Exception:
            try:
                import google.generativeai as genai
                genai_name = "google.generativeai"
            except Exception:
                genai = None
                genai_name = None

# Explicitly configure genai to surface KeyError early
try:
    if genai is not None:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        logging.info("genai.configure called")
except KeyError as e:
    logging.error("GEMINI_API_KEY missing: %s", e)
    print(str(e))
except Exception as e:
    logging.exception("genai.configure failed: %s", str(e))
    print(str(e))


app = FastAPI(title="Motor de Diagnóstico - Backend")

# Temporary: allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    parts = [
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
        parts.insert(0, f"Machine ID: {req.machine_id}")
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
            if "output" in resp:
                return resp["output"]
            if "content" in resp:
                return resp["content"]
            if "message" in resp:
                m = resp["message"]
                if isinstance(m, dict):
                    return m.get("content") or m.get("text") or str(m)
                return str(m)
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
                return str(first)
        if hasattr(resp, "choices"):
            choices = getattr(resp, "choices")
            if choices:
                ch = choices[0]
                if hasattr(ch, "message") and hasattr(ch.message, "content"):
                    return ch.message.content
                if hasattr(ch, "content"):
                    return ch.content
        if hasattr(resp, "output_text"):
            return getattr(resp, "output_text")
        if hasattr(resp, "text"):
            return getattr(resp, "text")
        if hasattr(resp, "output"):
            return getattr(resp, "output")
    except Exception:
        pass

    try:
        return str(resp)
    except Exception:
        return ""


def call_gemini(prompt: str) -> str:
    # Local test mode returns canned JSON
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
            "maintenance_priority": 2,
        }
        return json.dumps(sample, ensure_ascii=False)

    if genai is None:
        raise RuntimeError("Nenhuma biblioteca GenAI disponível. Instale 'google-genai' ou 'google-generativeai'.")

    if "GEMINI_API_KEY" not in os.environ:
        raise RuntimeError("Variável de ambiente GEMINI_API_KEY não definida.")

    # Candidate model names (env override first)
    candidates = []
    if os.getenv("GEMINI_MODEL"):
        candidates.append(os.getenv("GEMINI_MODEL"))
    candidates.extend(["gemini-pro", "gemini-1.5-flash-latest", "gemini-1.5-flash", "gpt-4o-mini"])

    errors = []

    # Ensure genai configured again
    try:
        if hasattr(genai, "configure"):
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    except Exception as e:
        logging.exception("Failed to configure genai: %s", str(e))
        print(str(e))
        errors.append(f"configure: {type(e).__name__}: {str(e)}")

    # Try each candidate model
    for model_name in candidates:
        logging.info("Attempting model: %s", model_name)
        try:
            # GenerativeModel (new API)
            if hasattr(genai, "GenerativeModel"):
                try:
                    gm = genai.GenerativeModel(model_name)
                    if hasattr(gm, "generate_content"):
                        try:
                            resp = gm.generate_content(prompt)
                            text = _extract_text_from_resp(resp)
                            if text:
                                return text
                        except Exception as e:
                            logging.exception("GenerativeModel.generate_content error for %s: %s", model_name, str(e))
                            print(str(e))
                            errors.append(f"GenerativeModel.generate_content({model_name}): {type(e).__name__}: {str(e)}")
                    if hasattr(gm, "generate"):
                        try:
                            resp = gm.generate(prompt)
                            text = _extract_text_from_resp(resp)
                            if text:
                                return text
                        except Exception as e:
                            logging.exception("GenerativeModel.generate error for %s: %s", model_name, str(e))
                            print(str(e))
                            errors.append(f"GenerativeModel.generate({model_name}): {type(e).__name__}: {str(e)}")
                except Exception as e:
                    logging.exception("Failed to instantiate GenerativeModel(%s): %s", model_name, str(e))
                    print(str(e))
                    errors.append(f"GenerativeModel({model_name}): {type(e).__name__}: {str(e)}")

            # TextGenerationClient
            if hasattr(genai, "TextGenerationClient"):
                try:
                    client = genai.TextGenerationClient()
                    if hasattr(client, "generate_text"):
                        resp = client.generate_text(model=model_name, prompt=prompt)
                        text = _extract_text_from_resp(resp)
                        if text:
                            return text
                    if hasattr(client, "generate"):
                        resp = client.generate(model=model_name, prompt=prompt)
                        text = _extract_text_from_resp(resp)
                        if text:
                            return text
                except Exception as e:
                    logging.exception("TextGenerationClient error for %s: %s", model_name, str(e))
                    print(str(e))
                    errors.append(f"TextGenerationClient({model_name}): {type(e).__name__}: {str(e)}")

            # module-level generate_text
            if hasattr(genai, "generate_text"):
                try:
                    resp = genai.generate_text(model=model_name, prompt=prompt)
                    text = _extract_text_from_resp(resp)
                    if text:
                        return text
                except Exception as e:
                    logging.exception("genai.generate_text error for %s: %s", model_name, str(e))
                    print(str(e))
                    errors.append(f"generate_text({model_name}): {type(e).__name__}: {str(e)}")

            # chat completions (older package)
            try:
                if hasattr(genai, "chat") and hasattr(genai.chat, "completions"):
                    resp = genai.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}])
                    text = _extract_text_from_resp(resp)
                    if text:
                        return text
            except Exception as e:
                logging.exception("genai.chat.completions.create error for %s: %s", model_name, str(e))
                print(str(e))
                errors.append(f"chat.completions({model_name}): {type(e).__name__}: {str(e)}")

            # genai.text.generate
            try:
                if hasattr(genai, "text") and hasattr(genai.text, "generate"):
                    resp = genai.text.generate(model=model_name, prompt=prompt)
                    text = _extract_text_from_resp(resp)
                    if text:
                        return text
            except Exception as e:
                logging.exception("genai.text.generate error for %s: %s", model_name, str(e))
                print(str(e))
                errors.append(f"text.generate({model_name}): {type(e).__name__}: {str(e)}")

            # fallback genai.generate
            try:
                if hasattr(genai, "generate"):
                    resp = genai.generate(model=model_name, prompt=prompt)
                    text = _extract_text_from_resp(resp)
                    if text:
                        return text
            except Exception as e:
                logging.exception("genai.generate error for %s: %s", model_name, str(e))
                print(str(e))
                errors.append(f"generate({model_name}): {type(e).__name__}: {str(e)}")

        except Exception as outer_e:
            logging.exception("Unexpected error while attempting model %s: %s", model_name, str(outer_e))
            print(str(outer_e))
            errors.append(f"modelloop({model_name}): {type(outer_e).__name__}: {str(outer_e)}")

    logging.error("All model candidates failed: %s", errors)
    raise RuntimeError("Erro ao chamar API Gemini. Detalhes: " + " | ".join(errors))


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
