import os
import json
import logging
import traceback
import tempfile
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
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
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
    usuario: Optional[str] = "Julio"
    machine_id: Optional[str] = None

class DiagnoseResponse(BaseModel):
    diagnosis: Dict[str, Any]
    raw_output: str

# --- FUNÇÃO DE CONEXÃO UNIVERSAL (SEGURA) ---

def get_db_connection():
    """Gerencia a conexão com o banco tratando as aspas e quebras de linha da Square Cloud."""
    
    # Busca as variáveis e remove as aspas que a Square Cloud exige no painel
    ca_raw = os.getenv("DB_CA_CERT", "")
    cert_raw = os.getenv("DB_CLIENT_CERT", "")
    key_raw = os.getenv("DB_CLIENT_KEY", "")

    # Limpeza profunda: remove aspas, espaços e garante que as quebras de linha sejam respeitadas
    ca_content = ca_raw.strip().strip('"').strip("'").replace('\\n', '\n')
    cert_content = cert_raw.strip().strip('"').strip("'").replace('\\n', '\n')
    key_content = key_raw.strip().strip('"').strip("'").replace('\\n', '\n')

    # Se estivermos no Linux (Square Cloud) OU se as variáveis existirem
    if os.name != 'nt' or (ca_content and cert_content):
        logging.info("🔧 Configurando conexão segura via arquivos temporários na Nuvem...")
        
        ca_f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.crt')
        cert_f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.pem')
        key_f = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.key')

        try:
            ca_f.write(ca_content); ca_f.flush()
            cert_f.write(cert_content); cert_f.flush()
            key_f.write(key_content); key_f.flush()

            conn = psycopg2.connect(
                DB_URL,
                sslmode="verify-full",
                sslrootcert=ca_f.name,
                sslcert=cert_f.name,
                sslkey=key_f.name
            )
            return conn, [ca_f.name, cert_f.name, key_f.name]
        except Exception as e:
            # Se falhar, limpa os arquivos para não deixar lixo
            for f in [ca_f.name, cert_f.name, key_f.name]:
                if os.path.exists(f): os.remove(f)
            raise e
    else:
        # APENAS se for Windows local e sem variáveis de ambiente
        logging.info("💻 Conectando via caminhos locais do Windows...")
        conn = psycopg2.connect(
            DB_URL,
            sslmode="verify-full",
            sslrootcert=r"C:\Users\julio\Downloads\ca-certificate.crt",
            sslcert=r"C:\Users\julio\Downloads\certificate.pem",
            sslkey=r"C:\Users\julio\Downloads\private-key.key"
        )
        return conn, []

# --- FUNÇÕES DE LÓGICA ---

def salvar_no_banco(req: DiagnoseRequest, parsed_json: Dict[str, Any]):
    conn = None
    tmp_files = []
    try:
        conn, tmp_files = get_db_connection()
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
        logging.info(f"🚀 [DATABASE] Sucesso ao salvar registro de {req.usuario}")
    except Exception as e:
        logging.error(f"❌ [DATABASE] Erro ao salvar: {e}")
    finally:
        if conn: conn.close()
        for f in tmp_files:
            if os.path.exists(f): os.remove(f)

@app.get("/history")
async def get_history(usuario: Optional[str] = None):
    conn = None
    tmp_files = []
    try:
        conn, tmp_files = get_db_connection()
        cur = conn.cursor()
        if usuario:
            cur.execute("SELECT id, equipamento, severidade, laudo_tecnico, criado_em, usuario, json_completo FROM historico_manutencao WHERE usuario = %s ORDER BY criado_em DESC", (usuario,))
        else:
            cur.execute("SELECT id, equipamento, severidade, laudo_tecnico, criado_em, usuario, json_completo FROM historico_manutencao ORDER BY criado_em DESC LIMIT 50")
        
        rows = cur.fetchall()
        cur.close()
        return [{
            "id": r[0], "equipment": r[1], "severity": r[2], 
            "diagnosis": r[3], "date": r[4].isoformat(), 
            "user": r[5], "full_data": r[6]
        } for r in rows]
    except Exception as e:
        logging.error(f"❌ [HISTORY] Erro ao buscar: {e}")
        return []
    finally:
        if conn: conn.close()
        for f in tmp_files:
            if os.path.exists(f): os.remove(f)

# --- RESTO DO CÓDIGO (DIAGNOSE / PROMPT) ---

def build_prompt(req: DiagnoseRequest) -> str:
    return f"""
    Aja como um Engenheiro de Manutenção Sênior e Especialista em Confiabilidade (RCM).
    Gere um LAUDO TÉCNICO EXAUSTIVO para o ativo: {req.equipment_name}.
    Inspetor Responsável: {req.usuario}
    SINTOMAS: {req.symptoms}

    RETORNE APENAS JSON:
    {{
      "summary": "Parecer técnico denso (mínimo 300 palavras)...",
      "severity": "critical|high|medium|low",
      "probable_causes": [{{ "cause": "...", "detail": "...", "likelihood": 90 }}],
      "recommended_actions": ["passo 1", "passo 2"],
      "impacto_operacional": "...",
      "seguranca_loto": "...",
      "componente_foco": "..."
    }}
    """

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
        
        if not raw: raise Exception("IA sem resposta.")
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