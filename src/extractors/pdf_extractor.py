from pathlib import Path
from typing import Dict, Optional
import PyPDF2

class PDFExtractor:
    def __init__(self, max_pages: Optional[int] = None):
        self.max_pages = max_pages

    def extract_text(self, pdf_path: Path) -> str:
        """Extrai texto do PDF."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            pages = len(reader.pages)
            limit = min(pages, self.max_pages) if self.max_pages else pages
            for i in range(limit):
                text += reader.pages[i].extract_text() + "\n"
            return text

    def extract_metadata(self, pdf_path: Path) -> Dict:
        """Extrai metadados básicos do PDF."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return {
                "total_pages": len(reader.pages),
                "title": reader.metadata.title,
                "author": reader.metadata.author,
            }