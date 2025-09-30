# Migrations do Banco de Dados

Este diretório contém as migrations SQL para configurar o banco de dados Supabase.

## Como Aplicar

### Opção 1: Via Supabase Dashboard (Recomendado)

1. Acesse seu projeto no [Supabase Dashboard](https://app.supabase.com)
2. Navegue até **SQL Editor** no menu lateral
3. Clique em **New Query**
4. Copie e cole o conteúdo de `001_initial_schema.sql`
5. Clique em **Run** para executar

### Opção 2: Via CLI do Supabase

```bash
# Instale o CLI do Supabase (se não tiver)
brew install supabase/tap/supabase

# Faça login
supabase login

# Link com seu projeto
supabase link --project-ref seu-project-ref

# Execute a migration
supabase db push
```

### Opção 3: Cópia Direta

```bash
# Copie o conteúdo da migration
cat migrations/001_initial_schema.sql

# Cole no SQL Editor do Supabase e execute
```

## Migrations Disponíveis

### 001_initial_schema.sql
- **Data**: 2025-09-30
- **Descrição**: Schema inicial do sistema
- **Cria**:
  - Tabela `editais` (dados principais dos editais)
  - Tabela `cargos` (cargos e salários)
  - Tabela `conteudo_programatico` (estrutura hierárquica)
  - Índices para performance
  - Comentários nas tabelas e colunas

## Estrutura das Tabelas

### editais
Tabela principal que armazena metadados e status do processamento.

**Campos principais:**
- `hash_arquivo` - Deduplicação por SHA-256
- `status` - processando | concluido | erro
- `texto_extraido` - Texto completo do PDF
- `conteudo_verticalizado_md` - Markdown estruturado pela LLM

### cargos
Relacionamento 1:N com editais.

**Campos principais:**
- `edital_id` - FK para editais
- `nome` - Nome do cargo
- `salario` - Salário em formato texto

### conteudo_programatico
Relacionamento 1:N com editais. Estrutura hierárquica de até 4 níveis.

**Campos principais:**
- `edital_id` - FK para editais
- `secao` - Seção do edital (ex: "Conhecimentos Básicos")
- `materia` - Matéria (ex: "PORTUGUÊS", "MATEMÁTICA")
- `nivel_1, nivel_2, nivel_3, nivel_4` - Numeração hierárquica
- `ordem` - Ordem sequencial no documento

## Verificação

Após executar a migration, verifique se as tabelas foram criadas:

```sql
-- Listar todas as tabelas
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public';

-- Verificar estrutura
\d editais
\d cargos
\d conteudo_programatico
```

## Rollback

Para remover as tabelas (CUIDADO - remove todos os dados):

```sql
DROP TABLE IF EXISTS conteudo_programatico CASCADE;
DROP TABLE IF EXISTS cargos CASCADE;
DROP TABLE IF EXISTS editais CASCADE;
```

## Próximas Migrations

Futuras migrations devem seguir o padrão:
- `002_nome_da_feature.sql`
- `003_nome_da_feature.sql`

Sempre incremente o número sequencial.