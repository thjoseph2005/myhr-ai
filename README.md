# myhr-ai

`myhr-ai` is a monorepo starter for an HR policy assistant that answers questions from a repository-managed knowledge base. PDFs live in `data/knowledge_base/`, the FastAPI backend indexes them for RAG, and the Next.js frontend provides a ChatGPT-like enterprise chat experience with citations.

## Repository Structure

```text
myhr-ai/
├── apps/web
├── services/api
├── infra/azure/container-apps
├── docs
├── scripts
└── data/knowledge_base
```

## Knowledge Base Folder

Place HR policy PDFs in:

- `data/knowledge_base/`

Recommended starter file:

- `data/knowledge_base/hr_policy.pdf`

Only PDF files are indexed right now. End users do not upload documents through the UI.

## Local Setup

1. Copy `.env.example` to `.env`.
2. If you do not have Azure resources yet, set `MOCK_AZURE_MODE=true`.
3. Place one or more HR policy PDFs in `data/knowledge_base/`.
4. Run `make setup`.

## Indexing

To scan the knowledge base folder and rebuild the index:

```bash
make ingest
```

That command reindexes every PDF under `data/knowledge_base/`.

The backend also exposes:

- `GET /health`
- `GET /api/documents/status`
- `POST /api/documents/reindex`
- `POST /api/chat`

`GET /api/documents/status` includes the configured knowledge base path, discovered documents, per-document indexed state, total indexed chunks, and the last indexed timestamp when available.

## Run Locally

Start backend and frontend together:

```bash
make dev
```

Or run them separately:

```bash
make dev-api
make dev-web
```

Local URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/health`

## Azure Configuration

Fill these values in `.env` when you are ready to use Azure:

- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_CHAT_DEPLOYMENT`
- `AZURE_OPENAI_EMBEDDING_DEPLOYMENT`
- `AZURE_SEARCH_ENDPOINT`
- `AZURE_SEARCH_API_KEY`
- `AZURE_SEARCH_INDEX_NAME`

The app uses mock retrieval/generation locally when `MOCK_AZURE_MODE=true` or when Azure credentials are missing.
The default knowledge base path points at `data/knowledge_base`, where `hr_policy.pdf` is the expected starter document.

## Docker

```bash
docker compose up --build
```

The compose stack mounts `./data` into the API container and points `KNOWLEDGE_BASE_PATH` at `/app/data/knowledge_base`.

## Extension Notes

- Add more PDFs to `data/knowledge_base/` and rerun reindexing.
- Add metadata filters later by extending the index schema with policy type, region, or department.
- Replace mock mode with Azure-backed retrieval once credentials are available.
- Add authentication and conversation persistence if you move beyond a personal/internal deployment.

## Documentation

- [Architecture](/Users/thomasjoseph/Documents/HRAgent/docs/architecture.md)
- [Ingestion](/Users/thomasjoseph/Documents/HRAgent/docs/ingestion.md)
