# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Visão Geral do Projeto

Sistema Python para processar editais de concursos públicos em PDF, extrair conteúdo programático e verticalizar usando LLMs via OpenRouter. Os dados são persistidos em Supabase (PostgreSQL).

## Comandos de Desenvolvimento

### Instalação

**Preferencial (UV):**
```bash
uv venv
source .venv/bin/activate  # Linux/Mac
uv pip install -r requirements.txt
```

**Alternativa (pip tradicional):**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### Execução
```bash
python main.py
```

### Variáveis de Ambiente (.env)
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL_PRIMARY=anthropic/claude-3-haiku  # Modelo primário
OPENROUTER_MODELS_FALLBACK=openai/gpt-4o-mini,meta-llama/llama-3.1-8b-instruct  # Fallbacks
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Arquitetura do Sistema

### Fluxo de Processamento Principal (main.py:EditalProcessor)

1. **Resolução de Fonte** (`_resolve_pdf_source`): Aceita caminho local ou URL
2. **Deduplicação por Hash**: Verifica se o edital já foi processado usando hash SHA-256 do arquivo
3. **Criação de Registro**: Cria entrada inicial no banco com status `processando`
4. **Extração de Texto**: PDFExtractor extrai texto completo e metadados básicos (número de páginas)
5. **Processamento LLM - Metadados**:
   - Usa apenas primeiros 15.000 caracteres para extração de metadados
   - Extrai: formato de prova, datas, valores, cargos, salários
   - Prompt: `build_metadata_prompt()` em `src/processors/prompt_templates.py:1`
6. **Processamento LLM - Verticalização**:
   - Processa texto completo para estruturar conteúdo programático
   - Gera markdown hierárquico com numeração original
   - Prompt: `build_verticalization_prompt()` em `src/processors/prompt_templates.py:21`
7. **Parsing e Persistência**:
   - Metadados salvos na tabela `editais`
   - Cargos extraídos e salvos em `cargos`
   - Markdown parseado em estrutura hierárquica (níveis 1-4) e salvo em `conteudo_programatico`
8. **Finalização**: Atualiza status, tempo de processamento e custo total

### Estrutura de Módulos

```
src/
├── extractors/           # Extração de PDFs
│   ├── pdf_extractor.py  # PyPDF2 para extração de texto
│   └── url_handler.py    # Download de PDFs via httpx
├── processors/           # Integração com LLMs
│   ├── llm_client.py     # Cliente OpenRouter com retry e fallback
│   └── prompt_templates.py # Templates de prompts para metadados e verticalização
├── database/             # Persistência Supabase
│   ├── models.py         # Dataclasses: Edital, Cargo, ConteudoProgramatico
│   ├── supabase_client.py # CRUD operations e queries complexas
│   └── queries.py        # (placeholder para queries adicionais)
├── utils/                # Utilitários
│   ├── logger.py         # Logging estruturado
│   └── file_hash.py      # Cálculo SHA-256
└── exporters/
    └── csv_exporter.py   # Exportação de dados (futuro)
```

### Models (src/database/models.py)

- **Edital**: Metadados do edital, texto extraído, status de processamento
- **Cargo**: Cargos do concurso com salários
- **ConteudoProgramatico**: Estrutura hierárquica (4 níveis) com ordem sequencial
- **StatusProcessamento**: Enum (processando, concluido, erro)

### Cliente LLM (src/processors/llm_client.py)

- Usa biblioteca `openai` apontando para OpenRouter (base_url override)
- Fallback automático entre modelos configurados via env vars
- Retry com backoff exponencial (tenacity)
- Tracking de custo acumulado (placeholder - implementar cálculo real por modelo)
- Método principal: `process_with_fallback(prompt, system_prompt) -> (content, model_used)`

### Supabase Client (src/database/supabase_client.py)

**Métodos importantes:**
- `edital_existe(hash_arquivo)`: Verifica duplicata
- `criar_edital(edital) -> id`: Cria registro inicial
- `atualizar_edital(id, dados)`: Atualiza campos do edital
- `finalizar_processamento(id, sucesso, erro, dados_extras)`: Marca conclusão/erro
- `inserir_cargos(cargos)`: Batch insert de cargos
- `inserir_conteudo_programatico(conteudos, batch_size=100)`: Batch insert em lotes
- `buscar_editais_recentes(limite)`: Lista editais processados
- `buscar_conteudo_por_materia(edital_id, materia)`: Busca tópicos por matéria
- `estatisticas_processamento()`: Estatísticas agregadas (total, concluídos, erros, custo)

### Parsing de Conteúdo Programático (main.py:182)

O método `_parse_conteudo_programatico()` converte o markdown retornado pela LLM em registros estruturados:

- Detecta seções (`## Seção`) e matérias (`### MATÉRIA`)
- Usa regex para extrair numeração hierárquica (1, 1.1, 1.1.1, 1.1.1.1)
- Mapeia numeração em 4 níveis (nivel_1 a nivel_4)
- Mantém ordem sequencial dos itens
- Fallback para itens sem numeração

**Padrões regex suportados:**
- `1.2.3. Descrição` (ponto final)
- `1.2.3) Descrição` (parêntese)
- `1.2.3 - Descrição` (traço)
- `1.2.3 Descrição` (espaço direto)

## Pontos de Atenção

- **Deduplicação**: Sistema usa hash de arquivo, não URL. Mesmo edital baixado de URLs diferentes não será reprocessado
- **Limitação de Páginas**: `max_pages` pode ser usado para testes (default: None = todas)
- **Custo LLM**: Campo `custo_total_usd` atualmente usa placeholder. Implementar cálculo real baseado em tokens e modelo
- **Schema Supabase**: Não há migrations no repositório. Schema deve ser criado manualmente no Supabase (ver README:35)
- **Parsing de Metadados**: LLM pode retornar JSON envolto em markdown code blocks (```json). O método `_parse_metadata_json()` limpa isso antes de parsear

## Documentação e Estilo

- Todos os comentários, docstrings e mensagens de log devem ser em pt-br
- PRs devem mencionar @coderabbitai para review automatizado