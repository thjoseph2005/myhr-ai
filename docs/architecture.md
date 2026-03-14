# Architecture Overview

## Design Goals

- Ground every answer in indexed HR policy content.
- Keep frontend and backend independently deployable.
- Support a repository-managed knowledge base folder today without blocking multi-document expansion.
- Minimize cloud spend by keeping infrastructure and model choices small.

## Backend Flow

1. The frontend sends a question and lightweight chat history to FastAPI.
2. The backend retrieves chunks from the indexed repository knowledge base.
3. In Azure mode, embeddings and retrieval use Azure OpenAI and Azure AI Search.
4. In local mock mode, the same abstractions fall back to a lightweight local index for development.
5. The backend builds a grounded prompt that includes only retrieved excerpts.
6. The backend returns the answer plus citations for each supporting chunk.

## Index Strategy

Each chunk stored in the index includes:

- `id`
- `document_id`
- `document_name`
- `page_number`
- `chunk_number`
- `content`
- `content_vector`

This makes it easy to:

- support multiple PDFs later
- filter by document
- attach page-based citations in the UI

## Cost Controls

- Use a small chat deployment and small embedding deployment.
- Chunk conservatively to reduce embedding volume.
- Retrieve only the top few relevant chunks.
- Avoid database dependencies until conversation persistence is necessary.
- Allow mock mode before Azure resources are provisioned.

## Security Defaults

- Secrets come from environment variables only.
- CORS is explicit, not wildcarded.
- Errors are logged with request correlation but do not expose internals to clients.
