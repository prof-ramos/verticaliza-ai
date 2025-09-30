# 🚀 Guia de Instalação - Verticaliza-AI

Este guia apresenta a forma mais rápida de configurar e executar o Verticaliza-AI.

## ⚡ Instalação Rápida (Setup Automatizado)

Execute o script de setup automatizado que configura todo o ambiente:

```bash
./setup.sh
```

O script irá:
- ✅ Instalar UV (gerenciador de pacotes Python)
- ✅ Criar ambiente virtual
- ✅ Instalar todas as dependências (45 pacotes)
- ✅ Criar diretórios necessários (input_pdfs, temp, logs)
- ✅ Configurar arquivo .env
- ✅ Configurar Supabase (opcional - automático ou manual)

### Pré-requisitos

- **macOS ou Linux**
- **Conexão com internet**
- **Bash shell**

### Durante o Setup

O script irá solicitar:

1. **OpenRouter API Key**
   - Obtenha em: https://openrouter.ai/keys
   - Necessária para processar editais com IA

2. **Configuração do Supabase** (escolha uma opção):
   - **Opção 1 (Recomendada)**: Configuração automática via CLI
     - Faz login no Supabase
     - Permite criar novo projeto ou usar existente
     - Aplica o schema automaticamente

   - **Opção 2**: Configuração manual
     - Você fornece URL e API Key do seu projeto
     - Schema deve ser aplicado manualmente

   - **Opção 3**: Pular
     - Configure depois editando `.env`
     - Execute o schema manualmente

### Após o Setup

1. **Verifique as credenciais** no arquivo `.env`
2. **Coloque PDFs** no diretório `input_pdfs/`
3. **Execute a aplicação**:
   ```bash
   source .venv/bin/activate
   python main.py
   ```

## 📋 Instalação Manual

Se preferir fazer a instalação passo a passo, siga o [README.md](README.md).

## 🔧 Configuração do Supabase

### Opção 1: CLI do Supabase (Automático)

```bash
./scripts/setup_supabase.sh
```

### Opção 2: Manual via Dashboard

1. Acesse https://app.supabase.com
2. Crie um novo projeto ou use um existente
3. Vá em **SQL Editor**
4. Execute o conteúdo de `migrations/001_initial_schema.sql`
5. Copie as credenciais para `.env`:
   - **URL**: Settings → API → Project URL
   - **Anon Key**: Settings → API → Project API keys → anon/public

## 🧪 Testando a Instalação

```bash
# Ativar ambiente virtual
source .venv/bin/activate

# Verificar que todas as dependências estão instaladas
python -c "import PyPDF2, httpx, openai, supabase; print('✅ Todas as dependências OK')"

# Verificar .env
cat .env | grep -v "your-" && echo "✅ Credenciais configuradas" || echo "⚠️  Configure as credenciais no .env"

# Colocar um PDF em input_pdfs/ e executar
python main.py
```

## ❓ Problemas Comuns

### "UV not found"
```bash
# Instale manualmente
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### "Permission denied"
```bash
chmod +x setup.sh
chmod +x scripts/setup_supabase.sh
```

### "Could not find table 'editais'"
- Execute o schema SQL no Supabase Dashboard
- Arquivo: `migrations/001_initial_schema.sql`

### "No module named 'PyPDF2'"
```bash
source .venv/bin/activate
uv pip install -r requirements.txt
```

### "OPENROUTER_API_KEY não configurada"
- Edite `.env` e adicione sua chave da OpenRouter
- Obtenha em: https://openrouter.ai/keys

## 📞 Suporte

- **Documentação**: [README.md](README.md)
- **Arquitetura**: [CLAUDE.md](CLAUDE.md)
- **Migrations**: [migrations/README.md](migrations/README.md)
- **Issues**: https://github.com/seu-usuario/verticaliza-ai/issues

## 🎯 Próximos Passos

Após a instalação bem-sucedida:

1. Leia o [README.md](README.md) para entender as funcionalidades
2. Explore a [arquitetura do sistema](CLAUDE.md)
3. Coloque PDFs de editais em `input_pdfs/`
4. Execute `python main.py` e aguarde o processamento
5. Consulte os dados processados no Supabase Dashboard