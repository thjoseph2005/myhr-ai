from pathlib import Path
import re

from app.domain.models import IndexedDocument


class FolderScanningService:
    def __init__(self, knowledge_base_path: Path) -> None:
        self.knowledge_base_path = knowledge_base_path

    def discover_documents(self) -> list[IndexedDocument]:
        self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
        document_paths = sorted(
            path
            for path in self.knowledge_base_path.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        )
        return [
            IndexedDocument(
                document_id=re.sub(r"[^a-z0-9]+", "-", path.stem.lower()).strip("-"),
                document_name=path.name,
                path=str(path),
            )
            for path in document_paths
        ]
