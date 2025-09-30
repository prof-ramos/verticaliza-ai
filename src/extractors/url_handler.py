import requests
from pathlib import Path
from contextlib import contextmanager

@contextmanager
def URLHandler():
    """Context manager para download de PDFs."""
    yield URLDownloader()

class URLDownloader:
    def download_pdf(self, url: str, output_path: Path) -> bool:
        """Baixa PDF de URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            return True
        except Exception as e:
            print(f"Erro ao baixar PDF: {e}")
            return False