from pathlib import Path

import argparse

from app.core.config import get_settings
from app.services.document_service import DocumentService


def main() -> None:
    parser = argparse.ArgumentParser(description="Reindex all PDFs from the knowledge base folder.")
    parser.add_argument(
        "--path",
        required=False,
        help="Optional override for the knowledge base directory",
    )
    args = parser.parse_args()

    settings = get_settings()
    if args.path:
        settings.knowledge_base_path = str(Path(args.path))

    service = DocumentService(settings)
    result = service.reindex()
    print(
        f"Indexed {result.indexed_documents} documents and {result.indexed_chunks} chunks from "
        f"{settings.knowledge_base_path}"
    )


if __name__ == "__main__":
    main()
