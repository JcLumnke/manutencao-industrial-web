import os
import json
import logging
import traceback
import time
import psycopg2  # Importado para conexão com a Square Cloud
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configurações de Log
logging.basicConfig(level=logging.INFO)

# --- CONFIGURAÇÕES DO BANCO SQUARE CLOUD ---
DB_URL = "postgresql://squarecloud:TZeCqGnuCOEeqAuJ7hfgPNKG@square-cloud-db-ba4b27ddd83a41578b0a9853e83c7116.squareweb.app:7116/squarecloud"

# Ajuste automático de caminhos para os certificados
SSL_ROOT = r"C:\Users\julio\Downloads\ca-certificate.crt" if os.name == 'nt' else "/application/ca-certificate.crt"
SSL_CERT = r"C:\Users\julio\Downloads\certificate.pem" if os.name == 'nt' else "/application/certificate.pem"
SSL_KEY = r"C:\Users\julio\Downloads\private-key.key" if os.name == 'nt' else "/application/private-key.key"

# Configuração do Gemini
try:
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except Exception as e:
    logging.error("Falha ao configurar Gemini: %s", str(e))
    genai = None

app = FastAPI(title="Motor de Diagnóstico Industrial - Cloud Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- MODELOS DE DADOS ---
class DiagnoseRequest(BaseModel):
    symptoms: str = Field(..., description="Descrição dos sintomas")
    equipment_name: Optional[str] = "Equipamento Não Identificado"
    machine_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class DiagnoseResponse(BaseModel):
    diagnosis: Dict[str, Any]
    raw_output: str

# --- FUNÇÕES AUXILIARES ---

def _extract_text_from_resp(resp: Any) -> str:
    """Extrai texto de diferentes formatos de resposta do Gemini SDK."""
    try:
        if isinstance(resp, dict):
            if "candidates" in resp and resp["candidates"]:
                c = resp["candidates"][0]
                return c.get("content", {}).get("parts", [{}])[0].get("text", "")
        if hasattr(resp, "text"): return resp.text
        if hasattr(resp, "candidates") and resp.candidates:
            return resp.candidates[0].content.parts[0].text
    except Exception: pass
    return str(resp)

def salvar_no_banco(req: DiagnoseRequest, parsed_json: Dict[str, Any]):
    try:
        conn = psycopg2.connect(
            DB_URL,
            sslmode="verify-full",
            sslrootcert=SSL_ROOT,
            sslcert=SSL_CERT,
            sslkey=SSL_KEY
        )
        cur = conn.cursor()
        query = """
            INSERT INTO historico_manutencao 
            (equipamento, severidade, sintomas_usuario, laudo_tecnico, causas_provaveis, plano_acao, json_completo)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(query, (
            req.equipment_name,
            parsed_json.get("severity", "medium"),
            req.symptoms,
            str(parsed_json.get("summary", "Sem laudo disponível")),
            json.dumps(parsed_json.get("probable_causes", [])),
            json.dumps(parsed_json.get("recommended_actions", [])),
            json.dumps(parsed_json)
        ))
        conn.commit()
        cur.close()
        conn.close()
        logging.info("🚀 [DATABASE] Registro salvo na Square Cloud com sucesso!")
    except Exception as e:
        logging.error("❌ [DATABASE] Erro ao salvar na nuvem: %s", str(e))

def build_prompt(req: DiagnoseRequest) -> str:
    """Prompt de Engenheiro Sênior Densificado e Técnico."""
    query_id = int(time.time())
    
    parts = [
        f"### PROTOCOLO TÉCNICO DE ANÁLISE: {query_id} ###",
        f"ATIVO (EQUIPAMENTO): {req.equipment_name}",
        "PERFIL: Engenheiro de Manutenção Sênior (Especialista em RCM e Análise de Falhas (RCA)).",
        "CONTEXTO: Diagnóstico industrial de alta confiabilidade para tomada de decisão.",
        "IDIOMA: RESPONDA EXCLUSIVAMENTE EM PORTUGUÊS DO BRASIL.",
        
        "DIRETRIZES DE RESPOSTA (DENSIDADE TÉCNICA É OBRIGATÓRIA):",
        "1. No campo 'summary', NÃO resuma apenas o que eu disse. Cite terminologia técnica aplicável ao ativo (ex: harmonic distortion, cavitation, harmonic distortion, desalinhamento paralelo/angular, folga mecânica). Cite possíveis NORMAS ISO aplicáveis se relevante (ex: ISO 10816 para vibração).",
        "2. Identifique a 'severity' (baixa, média, alta, crítica) baseada no Risco de Parada de Produção e Risco à Segurança.",
        "3. No campo 'recommended_actions', forneça PASSOS TÉCNICOS sequenciais de reparo e bloqueio (LOTO - Lockout/Tagout). Não dê passos genéricos.",
        "4. No campo 'component', identifique o componente crítico afetado (ex: Rolamento 6205, Acoplamento, Estator, Bomba Hidráulica).",
        
        "GERE UM ÚNICO OBJETO JSON PURO COM ESTES CAMPOS EXATOS:",
        "- summary: Diagnóstico técnico denso em bullet points.",
        "- probable_causes: lista de {cause: string (citação técnica), likelihood: 0-100}",
        "- severity: low|medium|high|critical",
        "- recommended_actions: passos técnicos sequenciais de reparo.",
        "- component: componente afetado.",
        "- estimated_parts: peças e ferramentas que provavelmente serão necessárias.",
        "- troubleshooting_steps: sequência lógica para isolar a falha.",
        
        "RETORNE APENAS O JSON, SEM FORMATAÇÃO MARKDOWN (NÃO use ```json).",
        f"SINTOMAS RELATADOS PELO OPERADOR: {req.symptoms}"
    ]
    
    # Adicionando metadados se houver (para densificar mais)
    if req.metadata:
        parts.append("DADOS DE TELEMETRIA ADICIONAIS:")
        parts.append(json.dumps(req.metadata, ensure_ascii=False))
        
    return "\n".join(parts)

def extract_json_from_text(text: str):
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try: return json.loads(text[start:end+1])
            except Exception: pass
    raise ValueError("Falha na extração de dados técnicos da IA.")

@app.get("/")
async def root():
    return {"status": "Sistema de Manutenção Online", "database": "Square Cloud Connected"}

@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    prompt = build_prompt(req)
    try:
        raw = None
        last_exc = None
        for model_name in ("gemini-2.0-flash", "gemini-flash-latest"):
            try:
                logging.info(f"🤖 Tentando modelo: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                text = getattr(response, "text", None) or _extract_text_from_resp(response)
                raw = text if isinstance(text, str) else json.dumps(text)
                break
            except Exception as e:
                last_exc = e
                logging.warning(f"⚠️ Falha no modelo {model_name}: {e}")
                continue
        
        if raw is None: raise last_exc
        parsed = extract_json_from_text(raw)
        salvar_no_banco(req, parsed)
        return {"diagnosis": parsed, "raw_output": raw}
    except Exception as e:
        logging.error("Erro no processamento: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)