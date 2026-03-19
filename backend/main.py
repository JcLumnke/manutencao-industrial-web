import os
import json
import logging
import traceback
import time
import psycopg2
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configurações de Log
logging.basicConfig(level=logging.INFO)

# --- CONFIGURAÇÕES DO BANCO SQUARE CLOUD ---
DB_URL = "postgresql://squarecloud:TZeCqGnuCOEeqAuJ7hfgPNKG@square-cloud-db-ba4b27ddd83a41578b0a9853e83c7116.squareweb.app:7116/squarecloud"

# Configuração do Gemini
try:
    import google.generativeai as genai
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
except Exception as e:
    logging.error("Falha ao configurar Gemini: %s", str(e))
    genai = None

app = FastAPI(title="Motor de Diagnóstico Industrial - Edição Sênior")

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
    usuario: Optional[str] = "Julio" # Campo para identificar o autor do laudo
    machine_id: Optional[str] = None

class DiagnoseResponse(BaseModel):
    diagnosis: Dict[str, Any]
    raw_output: str

# --- FUNÇÕES AUXILIARES ---

def salvar_no_banco(req: DiagnoseRequest, parsed_json: Dict[str, Any]):
    """Salva o diagnóstico na Square Cloud com adaptação de ambiente (Local vs Nuvem)."""
    try:
        # Detecta se está rodando no seu Windows (nt) ou na Square Cloud (posix/linux)
        if os.name == 'nt':
            # Configuração para o seu COMPUTADOR LOCAL (Downloads)
            conn = psycopg2.connect(
                DB_URL,
                sslmode="verify-full",
                sslrootcert=r"C:\Users\julio\Downloads\ca-certificate.crt",
                sslcert=r"C:\Users\julio\Downloads\certificate.pem",
                sslkey=r"C:\Users\julio\Downloads\private-key.key"
            )
        else:
            # Configuração para a SQUARE CLOUD (Conexão interna segura)
            # 'require' criptografa a conexão sem exigir arquivos físicos que não existem na nuvem
            conn = psycopg2.connect(
                DB_URL,
                sslmode="require"
            )

        cur = conn.cursor()
        
        query = """
            INSERT INTO historico_manutencao 
            (equipamento, severidade, sintomas_usuario, laudo_tecnico, causas_provaveis, plano_acao, json_completo, usuario)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        cur.execute(query, (
            req.equipment_name,
            parsed_json.get("severity", "medium"),
            req.symptoms,
            str(parsed_json.get("summary", "")),
            json.dumps(parsed_json.get("probable_causes", [])),
            json.dumps(parsed_json.get("recommended_actions", [])),
            json.dumps(parsed_json),
            req.usuario 
        ))
        
        conn.commit()
        cur.close()
        conn.close()
        logging.info(f"🚀 [DATABASE] Registro do técnico {req.usuario} salvo com sucesso!")
    except Exception as e:
        logging.error("❌ [DATABASE] Erro ao salvar: %s", str(e))

def build_prompt(req: DiagnoseRequest) -> str:
    """Prompt densificado para gerar laudos técnicos de nível A4."""
    return f"""
    Aja como um Engenheiro de Manutenção Sênior e Especialista em Confiabilidade (RCM).
    Gere um LAUDO TÉCNICO EXAUSTIVO para o ativo: {req.equipment_name}.
    Inspetor Responsável: {req.usuario}

    DIRETRIZES DE DENSIDADE (PARA PREENCHER UMA PÁGINA):
    1. O campo 'summary' deve ser um parecer técnico profundo (mínimo de 300 palavras). 
       Explique a física da falha, mencione termos como ressonância, fadiga de material ou cavitação conforme o caso.
    2. Em 'probable_causes', detalhe a causa raiz técnica (RCA) para cada item.
    3. Em 'recommended_actions', liste passos detalhados incluindo ferramentas (ex: alinhador a laser, megômetro) e normas (ISO/ABNT).
    4. Adicione campos de 'impacto_operacional' e 'seguranca_loto'.

    SINTOMAS: {req.symptoms}

    RETORNE APENAS O OBJETO JSON (SEM MARKDOWN):
    {{
      "summary": "Parecer técnico denso e detalhado...",
      "severity": "critical|high|medium|low",
      "probable_causes": [{{ "cause": "...", "detail": "explicação técnica", "likelihood": 90 }}],
      "recommended_actions": ["passo 1: bloqueio LOTO", "passo 2: inspeção com ferramenta X"],
      "impacto_operacional": "Descrição do risco de parada de planta",
      "seguranca_loto": "Procedimento de segurança obrigatório",
      "componente_foco": "Peça ou subsistema específico"
    }}
    """

# --- ENDPOINTS ---

@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    prompt = build_prompt(req)
    try:
        raw = None
        for model_name in ("gemini-2.0-flash", "gemini-flash-latest"):
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                raw = response.text
                if raw: break
            except: continue
        
        if not raw: raise Exception("IA não retornou dados.")

        raw = raw.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)

        salvar_no_banco(req, parsed)
        return {"diagnosis": parsed, "raw_output": raw}
    
    except Exception as e:
        logging.error("Erro: %s", traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)