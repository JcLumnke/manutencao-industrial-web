import psycopg2

# Trocamos 'postgres' pelo seu usuário, que é o nome do seu banco real na Square Cloud
NOME_DO_BANCO = "squarecloud" 
URL_BASE = f"postgresql://squarecloud:TZeCqGnuCOEeqAuJ7hfgPNKG@square-cloud-db-ba4b27ddd83a41578b0a9853e83c7116.squareweb.app:7116/{NOME_DO_BANCO}"

ca_root = r"C:\Users\julio\Downloads\ca-certificate.crt"
client_cert = r"C:\Users\julio\Downloads\certificate.pem"
client_key = r"C:\Users\julio\Downloads\private-key.key"

try:
    print(f"🚀 Conectando ao SEU banco exclusivo: {NOME_DO_BANCO}...")
    conn = psycopg2.connect(
        URL_BASE,
        sslmode="verify-full",
        sslrootcert=ca_root,
        sslcert=client_cert,
        sslkey=client_key
    )
    cur = conn.cursor()

    print("🏗️ Criando a tabela de 10GB...")
    # Aqui usamos o 'public' do SEU banco, onde você manda!
    cur.execute("""
        CREATE TABLE IF NOT EXISTS historico_manutencao (
            id SERIAL PRIMARY KEY,
            data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            equipamento VARCHAR(255) NOT NULL,
            severidade VARCHAR(50) NOT NULL,
            sintomas_usuario TEXT,
            laudo_tecnico TEXT NOT NULL,
            causas_provaveis JSONB,
            plano_acao JSONB,
            json_completo JSONB
        );
    """)
    
    conn.commit()
    print("\n✅ VITÓRIA TOTAL, JULIO! A tabela foi criada no seu banco 'squarecloud'!")
    
    cur.close()
    conn.close()

except Exception as e:
    print(f"\n❌ Erro: {e}")
    print("\n💡 Se der erro de 'database does not exist', olhe no seu painel")
    print("o nome exato que está no campo 'Database' e troque no código.")