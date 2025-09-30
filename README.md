# Verticaliza-AI

Sistema inteligente para processar editais de concursos públicos em PDF, extrair conteúdo programático e verticalizar usando LLMs via OpenRouter. Persistência em Supabase (PostgreSQL) com deduplicação por hash e fallback automático entre modelos.

## 🚀 Funcionalidades

- ✅ Extração de texto de PDFs (caminho local ou URL)
- ✅ Processamento inteligente com LLM (OpenRouter) com fallback automático
- ✅ Extração de metadados: datas, valores, cargos, salários, formato de prova
- ✅ Verticalização hierárquica do conteúdo programático (4 níveis)
- ✅ Persistência em Supabase com estrutura relacional
- ✅ Deduplicação automática via hash SHA-256 de arquivo
- ✅ Tracking de custos e tempo de processamento
- ✅ Retry automático com backoff exponencial

## 📋 Pré-requisitos

- Python 3.10+
- Conta no [OpenRouter](https://openrouter.ai) com API key
- Projeto no [Supabase](https://supabase.com) configurado

## 🔧 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/verticaliza-ai.git
cd verticaliza-ai
```

### 2. Configure o ambiente virtual

**Opção 1: UV (recomendado)**
```bash
# Instale UV se ainda não tiver: https://github.com/astral-sh/uv
uv venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate no Windows
```

**Opção 2: venv tradicional**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate no Windows
```

### 3. Instale as dependências

**Com UV:**
```bash
uv pip install -r requirements.txt
```

**Com pip:**
```bash
pip install -r requirements.txt
```

### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
# OpenRouter
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL_PRIMARY=anthropic/claude-3-haiku
OPENROUTER_MODELS_FALLBACK=openai/gpt-4o-mini,meta-llama/llama-3.1-8b-instruct

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. Configure o banco de dados Supabase

Execute o seguinte schema SQL no SQL Editor do Supabase:

```sql
-- Tabela principal de editais
CREATE TABLE editais (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hash_arquivo TEXT UNIQUE NOT NULL,
    nome_arquivo TEXT NOT NULL,
    url_origem TEXT,
    tamanho_bytes BIGINT,
    total_paginas INTEGER,
    status TEXT NOT NULL DEFAULT 'processando',
    erro_mensagem TEXT,
    data_upload TIMESTAMPTZ DEFAULT NOW(),
    data_processamento TIMESTAMPTZ,
    tempo_processamento_segundos NUMERIC,
    custo_total_usd NUMERIC(10,4),
    modelo_usado TEXT,
    formato_prova TEXT,
    data_prova DATE,
    data_inscricao_inicio DATE,
    data_inscricao_fim DATE,
    valor_inscricao TEXT,
    detalhes_discursiva TEXT,
    texto_extraido TEXT,
    conteudo_verticalizado_md TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de cargos
CREATE TABLE cargos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edital_id UUID REFERENCES editais(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    salario TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de conteúdo programático
CREATE TABLE conteudo_programatico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edital_id UUID REFERENCES editais(id) ON DELETE CASCADE,
    secao TEXT,
    materia TEXT,
    descricao TEXT NOT NULL,
    nivel_1 TEXT,
    nivel_2 TEXT,
    nivel_3 TEXT,
    nivel_4 TEXT,
    ordem INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_editais_hash ON editais(hash_arquivo);
CREATE INDEX idx_editais_status ON editais(status);
CREATE INDEX idx_cargos_edital ON cargos(edital_id);
CREATE INDEX idx_conteudo_edital ON conteudo_programatico(edital_id);
CREATE INDEX idx_conteudo_materia ON conteudo_programatico(materia);
```

## 💻 Uso

### Processamento básico

```python
from main import EditalProcessor

processor = EditalProcessor()

# Processar PDF local
success = processor.process("caminho/para/edital.pdf")

# Processar PDF de URL
success = processor.process("https://exemplo.com/edital.pdf")

# Processar com limite de páginas (útil para testes)
success = processor.process("edital.pdf", max_pages=10)
```

### Consultar estatísticas

```python
from src.database.supabase_client import SupabaseManager

db = SupabaseManager()

# Estatísticas gerais
stats = db.estatisticas_processamento()
print(f"Total de editais: {stats['total_editais']}")
print(f"Concluídos: {stats['concluidos']}")
print(f"Erros: {stats['erros']}")
print(f"Custo total: US$ {stats['custo_total_usd']:.2f}")

# Editais recentes
editais = db.buscar_editais_recentes(limite=10)

# Buscar conteúdo por matéria
conteudo = db.buscar_conteudo_por_materia(
    edital_id="uuid-aqui",
    materia="Português"
)
```

### Executar o exemplo

```bash
python main.py
```

## 🏗️ Arquitetura

### Fluxo de Processamento

1. **Resolução de Fonte**: Aceita caminho local ou URL (download automático)
2. **Deduplicação**: Verifica hash SHA-256 do arquivo para evitar reprocessamento
3. **Extração de Texto**: PyPDF2 extrai texto completo e metadados
4. **Processamento LLM - Metadados**: Extrai formato de prova, datas, cargos, salários
5. **Processamento LLM - Verticalização**: Estrutura conteúdo programático em markdown hierárquico
6. **Parsing e Persistência**: Converte markdown em estrutura relacional com 4 níveis
7. **Finalização**: Atualiza status, tempo e custo total

### Estrutura de Diretórios

```
verticaliza-ai/
├── main.py                    # Orquestrador principal (EditalProcessor)
├── requirements.txt           # Dependências Python
├── .env                       # Variáveis de ambiente (não commitar!)
└── src/
    ├── extractors/            # Extração de PDFs
    │   ├── pdf_extractor.py   # PyPDF2
    │   └── url_handler.py     # Download via httpx
    ├── processors/            # Integração LLM
    │   ├── llm_client.py      # Cliente OpenRouter com fallback
    │   └── prompt_templates.py # Templates de prompts
    ├── database/              # Persistência Supabase
    │   ├── models.py          # Dataclasses (Edital, Cargo, etc)
    │   └── supabase_client.py # CRUD e queries
    ├── utils/                 # Utilitários
    │   ├── logger.py          # Logging estruturado
    │   └── file_hash.py       # SHA-256
    └── exporters/
        └── csv_exporter.py    # Exportação (futuro)
```

## 🎯 Modelos de Dados

### Edital
- Metadados do edital (nome, hash, URL, tamanho)
- Status de processamento (processando, concluido, erro)
- Informações extraídas (formato prova, datas, valores)
- Texto extraído e conteúdo verticalizado (markdown)
- Métricas (tempo, custo, modelo usado)

### Cargo
- Vinculado ao edital (FK)
- Nome do cargo
- Salário (texto livre)

### ConteudoProgramatico
- Vinculado ao edital (FK)
- Estrutura hierárquica de 4 níveis (nivel_1 a nivel_4)
- Seção e matéria
- Descrição do tópico
- Ordem sequencial

## ⚙️ Configuração Avançada

### Modelos LLM

O sistema usa fallback automático entre modelos. Configure em `.env`:

```env
OPENROUTER_MODEL_PRIMARY=anthropic/claude-3-haiku
OPENROUTER_MODELS_FALLBACK=openai/gpt-4o-mini,meta-llama/llama-3.1-8b-instruct
```

### Limites e Otimizações

- **Extração de metadados**: Usa apenas primeiros 15.000 caracteres (performance)
- **Verticalização**: Processa texto completo
- **Batch inserts**: Conteúdo programático inserido em lotes de 100 registros
- **Retry**: 3 tentativas com backoff exponencial (4-10 segundos)

## 🔍 Padrões de Numeração Suportados

O parser de conteúdo programático reconhece:

- `1.2.3. Descrição` (ponto final)
- `1.2.3) Descrição` (parêntese)
- `1.2.3 - Descrição` (traço)
- `1.2.3 Descrição` (espaço direto)

Até 4 níveis hierárquicos: `1`, `1.1`, `1.1.1`, `1.1.1.1`

## 🛠️ Desenvolvimento

### Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -m 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request mencionando @coderabbitai

### Estilo de Código

- Todos os comentários, docstrings e logs em **pt-br**
- Use type hints em funções públicas
- Docstrings no formato Google Style

## 📝 TODO / Roadmap

- [ ] Implementar cálculo real de custos por modelo/tokens
- [ ] Adicionar RLS (Row Level Security) no Supabase
- [ ] Criar API REST com FastAPI
- [ ] Dashboard de monitoramento
- [ ] Testes unitários e de integração
- [ ] CI/CD com GitHub Actions
- [ ] Exportação para CSV/Excel
- [ ] Suporte a OCR para PDFs escaneados

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🤝 Suporte

- Issues: [GitHub Issues](https://github.com/seu-usuario/verticaliza-ai/issues)
- Documentação: [CLAUDE.md](CLAUDE.md)

---

**Desenvolvido com ❤️ para facilitar o estudo para concursos públicos**