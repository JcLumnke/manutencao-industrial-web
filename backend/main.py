import os
import json
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)

# Try importing modern google.genai first, then fall back to older packages
genai = None
genai_name = None
try:
    from google import genai as genai  # preferred
    genai_name = 'google.genai'
except Exception:
    def call_gemini(prompt: str) -> str:
        # local test stub
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
            raise RuntimeError("Nenhuma biblioteca GenAI disponível. Instale 'google-genai' ou 'google-generativeai'.")

        if "GEMINI_API_KEY" not in os.environ:
            raise RuntimeError("Variável de ambiente GEMINI_API_KEY não definida.")

        # Candidate model names to try (env override first)
        env_model = os.getenv("GEMINI_MODEL")
        candidates = []
        if env_model:
            candidates.append(env_model)
        candidates.extend(["gemini-pro", "gemini-1.5-flash-latest", "gemini-1.5-flash", "gpt-4o-mini"])

        errors = []

        # ensure genai is configured
        try:
            if hasattr(genai, "configure"):
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
                logging.info("genai.configure(api_key=...) executed in call_gemini")
        except Exception as e:
            logging.exception("Failed to run genai.configure in call_gemini: %s", str(e))
            print(str(e))
            errors.append(f"configure: {type(e).__name__}: {str(e)}")

        # Try each candidate model name in sequence
        for model_name in candidates:
            logging.info("Attempting model: %s", model_name)
            try:
                # Try GenerativeModel if available
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

                # Try TextGenerationClient if available
                if hasattr(genai, "TextGenerationClient"):
                    try:
                        client = genai.TextGenerationClient()
                        # prefer generate_text or generate
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

                # Module-level generate_text
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

                # Older chat completions
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
        raise RuntimeError("Nenhuma biblioteca GenAI disponível. Instale 'google-genai' ou 'google-generativeai'.")

    if "GEMINI_API_KEY" not in os.environ:
        raise RuntimeError("Variável de ambiente GEMINI_API_KEY não definida.")

    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    errors = []

    # ensure genai is configured (attempt again with explicit os.environ access)
    try:
        if hasattr(genai, "configure"):
            genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            logging.info("genai.configure(api_key=...) executed in call_gemini")
    except Exception as e:
        logging.exception("Failed to run genai.configure in call_gemini: %s", str(e))
        print(str(e))
        errors.append(f"configure: {type(e).__name__}: {str(e)}")

    # Try GenerativeModel (preferred new API)
    if hasattr(genai, "GenerativeModel"):
        try:
            logging.info("Trying genai.GenerativeModel('%s')", model_name)
            gm = genai.GenerativeModel(model_name)
            if hasattr(gm, "generate_content"):
                try:
                    resp = gm.generate_content(prompt)
                    text = _extract_text_from_resp(resp)
                    if text:
                        return text
                except Exception as e:
                    logging.exception("GenerativeModel.generate_content error: %s", str(e))
                    print(str(e))
                    errors.append(f"GenerativeModel.generate_content: {type(e).__name__}: {str(e)}")
            if hasattr(gm, "generate"):
                try:
                    resp = gm.generate(prompt)
                    text = _extract_text_from_resp(resp)
                    if text:
                        return text
                except Exception as e:
                    logging.exception("GenerativeModel.generate error: %s", str(e))
                    print(str(e))
                    errors.append(f"GenerativeModel.generate: {type(e).__name__}: {str(e)}")
        except Exception as e:
            logging.exception("Failed to instantiate/use GenerativeModel: %s", str(e))
            print(str(e))
            errors.append(f"GenerativeModel: {type(e).__name__}: {str(e)}")

    # Try modern TextGenerationClient
    if hasattr(genai, "TextGenerationClient"):
        try:
            logging.info("Calling Gemini via TextGenerationClient")
            client = genai.TextGenerationClient()
            for kw in ("prompt", "input", "text", "messages"):
                try:
                    if hasattr(client, "generate_text"):
                        resp = client.generate_text(model=model_name, **{kw: prompt})
                    elif hasattr(client, "generate"):
                        resp = client.generate(model=model_name, **{kw: prompt})
                    else:
                        continue
                    text = _extract_text_from_resp(resp)
                    if text:
                        return text
                except TypeError:
                    continue
                except Exception as e:
                    logging.exception("TextGenerationClient call error: %s", str(e))
                    print(str(e))
                    errors.append(f"TextGenerationClient.call: {type(e).__name__}: {str(e)}")
        except Exception as e:
            logging.exception("Error creating TextGenerationClient: %s", str(e))
            print(str(e))
            errors.append(f"TextGenerationClient: {type(e).__name__}: {str(e)}")

    # module-level generate_text
    if hasattr(genai, "generate_text"):
        try:
            logging.info("Calling genai.generate_text()")
            resp = genai.generate_text(model=model_name, prompt=prompt)
            text = _extract_text_from_resp(resp)
            if text:
                return text
        except Exception as e:
            logging.exception("Error calling genai.generate_text: %s", str(e))
            print(str(e))
            errors.append(f"generate_text: {type(e).__name__}: {str(e)}")

    # Older chat completions
    try:
        if hasattr(genai, "chat") and hasattr(genai.chat, "completions"):
            logging.info("Calling genai.chat.completions.create()")
            resp = genai.chat.completions.create(model=model_name, messages=[{"role": "user", "content": prompt}])
            text = _extract_text_from_resp(resp)
            if text:
                return text
    except Exception as e:
        logging.exception("Error calling genai.chat.completions.create: %s", str(e))
        print(str(e))
        errors.append(f"chat.completions: {type(e).__name__}: {str(e)}")

    # older text.generate
    try:
        if hasattr(genai, "text") and hasattr(genai.text, "generate"):
            logging.info("Calling genai.text.generate()")
            resp = genai.text.generate(model=model_name, prompt=prompt)
            text = _extract_text_from_resp(resp)
            if text:
                return text
    except Exception as e:
        logging.exception("Error calling genai.text.generate: %s", str(e))
        print(str(e))
        errors.append(f"text.generate: {type(e).__name__}: {str(e)}")

    # general fallback: try genai.generate
    try:
        if hasattr(genai, "generate"):
            logging.info("Calling genai.generate() fallback")
            resp = genai.generate(model=model_name, prompt=prompt)
            text = _extract_text_from_resp(resp)
            if text:
                return text
    except Exception as e:
        logging.exception("Error calling genai.generate: %s", str(e))
        print(str(e))
        errors.append(f"generate: {type(e).__name__}: {str(e)}")

    logging.error("All Gemini call methods failed: %s", errors)
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
