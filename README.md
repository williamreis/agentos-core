# AgentOS Core

API em **FastAPI** para orquestração de agentes especializados, com autenticação por chave, RAG (FAISS + sentence-transformers) para o agente de FAQ e uma UI **Streamlit** somente leitura que lista agentes e ferramentas.

## Requisitos

- Python **3.12** (alinhado ao `Dockerfile`)
- Dependências em `requirements.txt` (inclui modelos de embedding; a primeira execução pode baixar pesos)

## Estrutura do repositório

| Caminho | Descrição |
|--------|-----------|
| `main.py` | Aplicação FastAPI: health, listagem de agentes e rotas `POST /agent/*` |
| `app/core/` | Registry de clientes, executor e lógica compartilhada |
| `app/agents/` | Implementações por domínio (ex.: fraud, faq) |
| `app/shared/` | Auth, logging, RAG |
| `app/models/schemas.py` | Esquemas Pydantic (ex.: corpo `AgentRequest`) |
| `data/` | Corpus para ingestão (`*.txt`, `*.pdf`) e artefatos RAG gerados |
| `scripts/ingest_rag.py` | Constrói índice FAISS a partir de `data/` |
| `ui/app.py` | Dashboard Streamlit (manifest dos agentes) |
| `tests/` | Testes com `pytest` e `TestClient` |

## Configuração

Copie o exemplo e ajuste as variáveis:

```bash
cp .env.example .env
```

Principais variáveis (ver `.env.example` para a lista completa):

- **`AUTH_ENABLED`** — `false` desliga a exigência de `Authorization` nos `POST /agent/*`.
- **`FRAUD_API_KEY`** / **`FAQ_API_KEY`** — chaves usadas quando a auth está ligada; cada chave só pode chamar o agente correspondente.
- **RAG** — após a ingestão, a API usa arquivos em `data/` (`rag_faiss.index`, `rag_chunks.json`, etc.). Opcionais: `RAG_MODEL`, `RAG_MIN_SIMILARITY`, `RAG_FORCE_KEYWORD`.
- **Fraude semântica** — `FRAUD_SEMANTIC_ENABLED` (e aliases documentados no `.env.example`) para classificador semântico opcional.

## Docker Compose

Sobe API e UI com volumes para desenvolvimento:

```bash
docker compose up --build
```

Portas padrão no host: **8000** (API) e **8501** (UI), sobrescrevíveis via `API_PORT`, `UI_PORT`, etc. (ver `.env.example`).

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Status e se a autenticação está habilitada |
| `GET` | `/agents` | Manifesto dos agentes (nome, descrição, tools) |
| `POST` | `/agent/fraud` | Agente de classificação de risco / fraude |
| `POST` | `/agent/faq` | Agente de respostas com RAG |

Corpo JSON:

```json
{ "input": "texto de entrada (1–16000 caracteres)" }
```

Quando `AUTH_ENABLED=true`, envie o header:

```http
Authorization: Bearer <FRAUD_API_KEY ou FAQ_API_KEY>
```

Também é aceito o valor da chave sem o prefixo `Bearer `. Opcionalmente: `X-App-Id` (repassado ao executor).

Documentação interativa: `http://localhost:8000/docs` (quando a API estiver em execução).

## RAG (FAQ)

1. Coloque arquivos `.txt` e/ou `.pdf` em `data/`.
2. Na raiz do projeto:

```bash
python -m scripts.ingest_rag
```

Isso gera/atualiza o índice FAISS e metadados em `data/`. Sem chunks extraídos, o comando encerra com erro orientando a adicionar fontes.

## Licença e contribuição

Defina no repositório conforme a política do projeto (não há `LICENSE` referenciado neste README).
