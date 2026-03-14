from pathlib import Path
import re

from pypdf import PdfReader

from app.domain.models import ExtractedPage


class PDFExtractionService:
    def extract_pages(self, file_path: Path) -> list[ExtractedPage]:
        reader = PdfReader(str(file_path))
        document_id = re.sub(r"[^a-z0-9]+", "-", file_path.stem.lower()).strip("-")
        document_name = file_path.name
        pages: list[ExtractedPage] = []

        for page_number, page in enumerate(reader.pages, start=1):
            pages.append(
                ExtractedPage(
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page_number,
                    text=page.extract_text() or "",
                )
            )

        return pages
