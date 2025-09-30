def build_metadata_prompt(text: str) -> str:
    """Prompt para extrair metadados do edital."""
    return f"""
Extraia as seguintes informações do edital em formato JSON válido:

{{
    "formato_prova": "objetiva/discursiva/mista",
    "data_prova": "YYYY-MM-DD",
    "data_inscricao_inicio": "YYYY-MM-DD",
    "data_inscricao_fim": "YYYY-MM-DD",
    "valor_inscricao": "R$ XXX,XX",
    "detalhes_discursiva": "descrição se houver",
    "cargos": ["Cargo 1", "Cargo 2"],
    "salarios": {{"Cargo 1": "R$ XXXX,XX", "Cargo 2": "R$ YYYY,YY"}}
}}

Texto do edital:
{text}
"""

def build_verticalization_prompt(text: str) -> str:
    """Prompt para verticalizar conteúdo programático."""
    return f"""
Estruture o conteúdo programático do edital em formato Markdown hierárquico.
Mantenha a numeração original e organize por seções e matérias.

Use o formato:
## Seção
### Matéria
1. Tópico nível 1
1.1 Subtópico nível 2
1.1.1 Sub-subtópico nível 3

Texto do edital:
{text}
"""