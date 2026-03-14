# Repository Guidelines

## Project Overview
- Project: `myhr-ai`
- Purpose: HR policy question-answering app using RAG over PDF content.
- Frontend: Next.js 14, TypeScript, Tailwind CSS.
- Backend: FastAPI, Python 3.11+.
- Retrieval: Azure OpenAI embeddings/chat and Azure AI Search vector retrieval.
- Deployment target: Azure Container Apps.

## Working Principles
- Preserve the clean architecture split in `services/api/app`.
- Keep the API contract in sync between `services/api` and `apps/web/src/types`.
- Prefer small, composable modules over large utility files.
- Keep cost-conscious defaults: low-overhead models, small chunk sizes, and conservative retrieval settings.
- Ground every answer in retrieved chunks and return citations with page numbers.

## Implementation Rules
- Do not hardcode secrets or environment-specific URLs.
- When changing retrieval behavior, update both runtime logic and README documentation.
- Add tests for meaningful backend business logic and frontend API adapters when behavior changes.
- Keep UI aligned with the established Merrill-inspired visual system in `apps/web/src/app/globals.css`.
- Maintain support for a single initial PDF in `data/HRPolicy.pdf`, but avoid assumptions that block future multi-document support.

## Local Workflow
- Use `make setup` for first-time local initialization.
- Use `make dev` to run frontend and backend together.
- Use `make test` before handing off substantial changes.
- If dependencies or SDK behavior are updated, refresh `.env.example` and README notes in the same change.
