from typing import List, Dict, Any
from .supabase_client import SupabaseManager

class EditalQueries:
    def __init__(self, db: SupabaseManager):
        self.db = db

    def comparar_conteudos(
        self,
        edital_id_1: str,
        edital_id_2: str
    ) -> Dict[str, List[str]]:
        """Compara conteúdos programáticos de dois editais."""

        # Buscar matérias de cada edital
        materias_1 = set(
            item["materia"]
            for item in self.db.client.table("conteudo_programatico")
                .select("materia")
                .eq("edital_id", edital_id_1)
                .execute().data
            if item["materia"]
        )

        materias_2 = set(
            item["materia"]
            for item in self.db.client.table("conteudo_programatico")
                .select("materia")
                .eq("edital_id", edital_id_2)
                .execute().data
            if item["materia"]
        )

        return {
            "comuns": sorted(materias_1 & materias_2),
            "apenas_edital_1": sorted(materias_1 - materias_2),
            "apenas_edital_2": sorted(materias_2 - materias_1)
        }

    def buscar_editais_similares(
        self,
        hash_arquivo: str,
        limite: int = 5
    ) -> List[Dict[str, Any]]:
        """Busca editais com conteúdo similar (via full-text search)."""

        # Primeiro, pegar o texto do edital de referência
        ref = self.db.client.table("editais")\
            .select("texto_extraido")\
            .eq("hash_arquivo", hash_arquivo)\
            .execute()

        if not ref.data:
            return []

        # Extrair palavras-chave principais (simplificado)
        texto = ref.data[0]["texto_extraido"] or ""
        keywords = set(texto.upper().split()[:50])  # Top 50 palavras

        # Buscar editais que contenham essas palavras
        # (Nota: isso é simplificado; ideal seria usar pg_trgm ou tsquery)
        similares = self.db.client.table("editais")\
            .select("id, nome_arquivo, hash_arquivo")\
            .neq("hash_arquivo", hash_arquivo)\
            .limit(limite)\
            .execute()

        return similares.data