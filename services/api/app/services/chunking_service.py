from app.domain.models import ChunkInput, ExtractedPage


class ChunkingService:
    def __init__(self, chunk_size: int = 1000, overlap: int = 150) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_pages(self, pages: list[ExtractedPage]) -> list[ChunkInput]:
        chunks: list[ChunkInput] = []
        for page in pages:
            for chunk_number, content in enumerate(self._chunk_text(page.text), start=1):
                chunks.append(
                    ChunkInput(
                        chunk_id=f"{page.document_id}-p{page.page_number}-c{chunk_number}",
                        document_id=page.document_id,
                        document_name=page.document_name,
                        page_number=page.page_number,
                        chunk_number=chunk_number,
                        content=content,
                    )
                )
        return chunks

    def _chunk_text(self, text: str) -> list[str]:
        normalized = " ".join(text.split())
        if not normalized:
            return []

        chunks: list[str] = []
        start = 0
        while start < len(normalized):
            end = min(start + self.chunk_size, len(normalized))
            chunks.append(normalized[start:end])
            if end == len(normalized):
                break
            start = max(end - self.overlap, start + 1)
        return chunks
