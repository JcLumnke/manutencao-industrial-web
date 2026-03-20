# ⚙️ SIMI — Sistema Inteligente de Manutenção Industrial

**Análise de Falhas em Tempo Real com IA Generativa (Google Gemini 2.0 Flash)**

O **SIMI** é uma plataforma avançada para otimização da manutenção industrial. Ele utiliza Inteligência Artificial Generativa para transformar relatos técnicos de sintomas em laudos estruturados, permitindo uma tomada de decisão rápida, técnica e baseada em dados de confiabilidade.

Este projeto foca na redução de *downtime* fabril por meio de diagnósticos instantâneos contendo:
* 🔎 **Causas Raiz (RCA):** Identificação física da falha e mecanismos de desgaste.
* ⚠️ **Nível de Severidade:** Classificação automática de criticidade (Crítica, Alta, Média, Baixa).
* 🛠️ **Plano de Ação:** Passos detalhados para reparo e normas de segurança (LOTO).

---

## 🏗️ 1. Arquitetura do Sistema

A aplicação segue uma arquitetura desacoplada (Frontend / Backend), garantindo escalabilidade e independência entre a interface e a inteligência de processamento.

### 🔄 Fluxo de Comunicação (Data Flow)

```mermaid
graph TD
    A[Frontend: React + Vite] -->|Requisições HTTP| B[Backend: FastAPI + Python]
    B -->|Prompt Sênior| C[Google Gemini 2.0 Flash]
    C -->|Fallback automático| E[Gemini-1.5-Flash]
    C -->|JSON Estruturado| B
    B -->|Persistência SSL| F[(PostgreSQL SquareCloud)]
    B -->|Laudo Validado| A
    A -->|Exportação| G[PDF Profissional]

    📂 2. Estrutura do Projeto
Mapeamento da estrutura atual do repositório:

/backend: API em FastAPI, integração com SDK Gemini e motor de diagnósticos.

/frontend: Dashboard React com suporte a exportação de PDF e histórico dinâmico.

/prompts: Engenharia de Prompt utilizada para garantir o comportamento de "Engenheiro Sênior".

main.py: Motor principal de diagnóstico e conexão segura com o banco de dados.

🛠️ 3. Stack Tecnológica
IA Generativa: Google Gemini 2.0 Flash (Modelo principal) e Gemini 1.5 Flash (Fallback).

Backend: Python 3.10+, FastAPI, Uvicorn e Psycopg2.

Frontend: React.js, Vite, jsPDF e AutoTable.

Banco de Dados: PostgreSQL (Hospedado na Square Cloud com conexão segura via SSL/TLS).

Deploy: Square Cloud (Backend/DB) e Vercel (Frontend).

🚧 4. Desafios Técnicos e Soluções
💾 Persistência de Dados e Segurança
O projeto utiliza uma instância de PostgreSQL hospedada na Square Cloud. A conexão é protegida via certificados SSL decodificados em tempo de execução através de strings Base64 configuradas nas variáveis de ambiente. Isso garante que nenhum dado sensível ou arquivo de certificado fique exposto no repositório.

📄 Exportação de Laudos Densos
Implementamos uma lógica de geração de documentos PDF (Padrão A4) que suporta pareceres técnicos de alta densidade (300+ palavras). Utilizamos o plugin jspdf-autotable configurado com quebra de linha automática para garantir que a explicação detalhada da "Física da Falha" seja apresentada de forma profissional.

🧠 Engenharia de Prompt (Chain-of-Thought)
O sistema utiliza um System Prompt robusto que define a persona de um Engenheiro de Manutenção Sênior. O modelo é forçado a raciocinar sobre os sintomas antes de classificar a severidade, utilizando formatos JSON para garantir integração imediata com o dashboard.

💻 5. Guia de Instalação Rápida
Backend
Entre na pasta backend.

Instale as dependências: pip install -r requirements.txt.

Configure o arquivo .env com sua GEMINI_API_KEY e as chaves Base64 do banco.

Execute: python main.py.

Frontend
Entre na pasta frontend.

Instale as dependências: npm install.

Execute: npm run dev.

👨‍💻 Autor
Julio Cesar Lumke
Projeto desenvolvido com foco em Inteligência Artificial aplicada à Confiabilidade Industrial.