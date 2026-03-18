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
SSL_ROOT = r"C:\Users\julio\Downloads\ca-certificate.crt"
SSL_CERT = r"C:\Users\julio\Downloads\certificate.pem"
SSL_KEY = r"C:\Users\julio\Downloads\private-key.key"

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

def salvar_no_banco(req: DiagnoseRequest, parsed_json: Dict[str, Any]):
    """Salva o diagnóstico técnico na Square Cloud com segurança SSL máxima."""
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
        
        # Extraindo dados do JSON da IA para colunas específicas
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
    """Prompt Técnico de Engenheiro Sênior para Vitrine Profissional."""
    query_id = int(time.time())
    
    parts = [
        f"### PROTOCOLO TÉCNICO: {query_id} ###",
        f"EQUIPAMENTO: {req.equipment_name}",
        "PERFIL: Engenheiro de Manutenção Sênior (Especialista em RCM e Confiabilidade).",
        "CONTEXTO: Diagnóstico industrial de alta precisão.",
        "IDIOMA: RESPONDA EXCLUSIVAMENTE EM PORTUGUÊS DO BRASIL.",
        
        "DIRETRIZES DE RESPOSTA:",
        "1. No campo 'summary', use terminologia técnica (ex: desalinhamento, cavitação, harmônicas).",
        "2. Identifique a 'severity' com base no risco de parada de linha.",
        "3. No campo 'recommended_actions', liste procedimentos técnicos e normas ISO/NBR se aplicável.",
        
        "GERE UM JSON PURO COM ESTES CAMPOS:",
        "- summary: Diagnóstico denso em bullet points.",
        "- probable_causes: lista de {cause: string, likelihood: 0-100}",
        "- severity: low|medium|high|critical",
        "- recommended_actions: sequência técnica de reparo.",
        "- component: subsistema afetado (ex: Acoplamento, Rolamento, Estator).",
        "- confidence: 0 a 1.",
        
        "REGRAS CRÍTICAS: NÃO use formatação Markdown. NÃO use ```json. RETORNE APENAS O OBJETO.",
        f"SINTOMAS: {req.symptoms}"
    ]
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

# --- ENDPOINTS ---

@app.get("/")
async def root():
    return {"status": "Sistema de Manutenção Online", "database": "Square Cloud Connected"}

@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    prompt = build_prompt(req)
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash") # Versão estável
        response = model.generate_content(prompt)
        raw_text = response.text
        
        # 1. Converte a resposta em JSON
        parsed = extract_json_from_text(raw_text)
        
        # 2. PERSISTÊNCIA NA NUVEM (O diferencial do seu projeto)
        salvar_no_banco(req, parsed)
        
        return {"diagnosis": parsed, "raw_output": raw_text}
    
    except Exception as e:
        logging.error("Erro no processamento: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)