# Verticaliza-AI

Sistema para processar editais de concursos públicos, extrair conteúdo programático e verticalizar usando IA.

## Funcionalidades

- Extração de texto de PDFs (local ou URL)
- Processamento com LLM (OpenRouter) para metadados e verticalização
- Persistência em Supabase (PostgreSQL)
- Evita reprocessamento via hash de arquivo
- API REST para consultas

## Instalação

1. Clone o repositório
2. Crie um ambiente virtual:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # ou venv\Scripts\activate no Windows
   ```

3. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure variáveis de ambiente no `.env`:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-xxxxx
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

5. Execute o schema SQL no Supabase (ver análise para detalhes)

## Uso

```python
from main import EditalProcessor

processor = EditalProcessor()
success = processor.process("caminho/para/edital.pdf", max_pages=50)
```

## Arquitetura

- **Extractors**: Extração de texto e metadados de PDFs
- **Processors**: Cliente LLM e templates de prompt
- **Database**: Models, cliente Supabase e queries
- **Utils**: Logger, hash de arquivos, etc.

## Próximos Passos

- Implementar RLS no Supabase
- Criar API REST com FastAPI
- Dashboard de monitoramento
- Testes de integração