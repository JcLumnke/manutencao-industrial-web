import os
import json
import logging
import traceback
import tempfile
import base64
import psycopg2
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configurações de Log
logging.basicConfig(level=logging.INFO)

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

class DiagnoseRequest(BaseModel):
    symptoms: str
    equipment_name: Optional[str] = "Equipamento"
    usuario: Optional[str] = "Julio"

class DiagnoseResponse(BaseModel):
    diagnosis: Dict[str, Any]
    raw_output: str

# --- FUNÇÃO DE CONEXÃO PROFISSIONAL (DECODIFICA BASE64) ---

def get_db_connection():
    """Lê o texto Base64 da Square Cloud e reconstrói os arquivos de certificado."""
    # Pega as tripas de letras que você colou no site
    ca_b64 = os.getenv("DB_CA_CERT", "").strip().strip('"')
    cert_b64 = os.getenv("DB_CLIENT_CERT", "").strip().strip('"')
    key_b64 = os.getenv("DB_CLIENT_KEY", "").strip().strip('"')

    # Se estiver na Square Cloud (onde as variáveis existem)
    if ca_b64 and cert_b64 and key_b64:
        logging.info("🔧 Decodificando certificados Base64 na Nuvem...")
        # Criamos arquivos temporários binários ('wb')
        ca_f = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.crt')
        cert_f = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pem')
        key_f = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.key')

        try:
            # Transforma as letras de volta nos arquivos originais
            ca_f.write(base64.b64decode(ca_b64)); ca_f.flush()
            cert_f.write(base64.b64decode(cert_b64)); cert_f.flush()
            key_f.write(base64.b64decode(key_b64)); key_f.flush()

            conn = psycopg2.connect(
                DB_URL,
                sslmode="verify-full",
                sslrootcert=ca_f.name,
                sslcert=cert_f.name,
                sslkey=key_f.name
            )
            return conn, [ca_f.name, cert_f.name, key_f.name]
        except Exception as e:
            for f in [ca_f.name, cert_f.name, key_f.name]:
                if os.path.exists(f): os.remove(f)
            raise e
    else:
        # Se você estiver rodando no seu computador (Local)
        logging.info("💻 Usando caminhos locais do Windows...")
        conn = psycopg2.connect(
            DB_URL,
            sslmode="verify-full",
            sslrootcert=r"C:\Users\julio\Downloads\ca-certificate.crt",
            sslcert=r"C:\Users\julio\Downloads\certificate.pem",
            sslkey=r"C:\Users\julio\Downloads\private-key.key"
        )
        return conn, []

# --- ROTAS E LÓGICA ---

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
        logging.info(f"🚀 [DATABASE] Sucesso! Registro salvo para {req.usuario}")
    except Exception as e:
        logging.error(f"❌ [DATABASE] Erro crítico: {e}")
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
        logging.error(f"❌ [HISTORY] Erro: {e}")
        return []
    finally:
        if conn: conn.close()
        for f in tmp_files:
            if os.path.exists(f): os.remove(f)

@app.post("/diagnose", response_model=DiagnoseResponse)
async def diagnose(req: DiagnoseRequest):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"Gere um laudo técnico para {req.equipment_name}. Sintomas: {req.symptoms}. Retorne apenas JSON."
        response = model.generate_content(prompt)
        raw = response.text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(raw)
        salvar_no_banco(req, parsed)
        return {"diagnosis": parsed, "raw_output": raw}
    except Exception as e:
        logging.error(f"Erro: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port)