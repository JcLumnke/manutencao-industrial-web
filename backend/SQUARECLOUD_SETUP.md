# Deploy na SquareCloud — instruções

1) Arquivos adicionados
- `squarecloud.app` — template de configuração da app (build/start). Veja [backend/squarecloud.app](backend/squarecloud.app).
- `.env.example` — placeholders para variáveis sensíveis. Veja [backend/.env.example](backend/.env.example).

2) Comandos recomendados (no painel SquareCloud)
- Build command: `pip install -r backend/requirements.txt`
- Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

3) Como definir `GEMINI_API_KEY` de forma segura

- No painel da SquareCloud: abra sua aplicação (ou crie uma nova).
- Vá para *Settings* → *Environment Variables* (ou seção equivalente).
- Adicione uma nova variável:
  - **Name**: `GEMINI_API_KEY`
  - **Value**: cole sua chave do Gemini (não compartilhe)
  - Se houver opção de marcar como *Secret* / *Protected*, habilite-a para ocultar o valor nos logs/UI.
- (Opcional) adicione `GEMINI_MODEL` se quiser forçar um modelo diferente.
- Salve e faça *Redeploy* / *Restart* da aplicação.

4) Boas práticas de segurança
- Nunca comite chaves no repositório. Use `.env.example` só como template.
- Use chaves distintas para desenvolvimento e produção. Guarde as chaves em um cofre de segredos quando possível.
- Rode testes com `GEMINI_TEST_MODE=1` (modo local) antes de ligar a chave de produção.
- Evite imprimir `GEMINI_API_KEY` nos logs. Se precisar de logs para debug, redija-os sem incluir valores sensíveis.
- Faça rotação periódica das chaves e limite permissões/escopo se a API suportar.

5) Verificação após deploy

- Após o deploy a SquareCloud fornece a URL oficial da app no painel (ex: `https://<sua-app>.squarecloud.app`).
- Teste com curl/HTTP client:

```bash
curl -X POST "https://<SUA_APP>/diagnose" \
  -H "Content-Type: application/json" \
  -d '{"symptoms":"vibração excessiva no eixo","machine_id":"M-1234"}'
```

- Se a app retornar JSON com `diagnosis` e `raw_output`, o backend está funcionando.

6) Observações finais
- Nosso `squarecloud.app` executa `pip install -r backend/requirements.txt` e inicia `uvicorn` apontando para `backend.main:app`. Se preferir, você pode mover dependências para um `requirements.txt` na raiz do projeto.
- Quando quiser, eu posso:
  - Ajudar a criar o deploy (passo a passo) pela UI do SquareCloud;
  - Preparar um `requirements.txt` no nível raiz para compatibilidade com outros deploys;
  - Prosseguir para o frontend no Vercel assim que você confirmar a URL do backend.
