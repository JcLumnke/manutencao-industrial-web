# Frontend — Vercel deploy

Projeto frontend minimal em Vite + React que consome o endpoint `/diagnose` do backend.

Como executar localmente

1. Na pasta `frontend`, instale dependências:

```bash
cd frontend
npm install
```

2. Defina a variável de ambiente `VITE_API_URL` (opcional — o app tem fallback para a URL do backend que você forneceu):

```bash
cp .env.example .env
# editar .env se necessário
```

3. Rodar em dev:

```bash
npm run dev
```

Build & Deploy no Vercel

1. Crie um novo projeto no Vercel e conecte ao seu repositório GitHub.
2. Configure as seguintes opções no painel do projeto:
   - **Framework preset**: Other
   - **Build command**: `npm run build`
   - **Output Directory**: `dist`
   - **Environment Variables**: defina `VITE_API_URL` com a URL do backend (ex: `https://manutencao-industrial-julio.squareweb.app`).
3. Deploy: clique em **Deploy**.

CORS

Se ocorrer erro de CORS ao chamar o backend a partir do navegador, você tem duas opções:

- Habilitar CORS no backend (FastAPI) e redeploy na SquareCloud. Posso aplicar esse patch para você.
- Ou criar uma Serverless Function no Vercel que faça proxy das requisições para o backend e evite problemas de CORS.
