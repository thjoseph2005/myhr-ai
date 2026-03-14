# Ingestion Notes

## Expected Input

Place one or more PDF files in:

- `data/knowledge_base/`

## Ingestion Pipeline

1. Scan the knowledge base folder for PDFs.
2. Read each PDF page by page.
2. Normalize and trim whitespace.
3. Split each page into overlapping chunks.
4. Generate embeddings for each chunk.
5. Rebuild the Azure AI Search index, or refresh the local mock index in development mode.
6. Upload or persist chunks in batches.

## Metadata Strategy

Each chunk includes document metadata and page number so the application can render citations. The current schema is folder-based and naturally supports multiple PDFs.

## Extending to Multiple PDFs

- Use a stable `document_id` derived from the file name or content hash.
- Ingest each PDF into the same index.
- Add UI filters later if you want users to target a specific policy set.
