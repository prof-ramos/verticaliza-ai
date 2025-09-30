#!/bin/bash

# ============================================================
# Verticaliza-AI - Setup Automatizado
# ============================================================
# Este script configura todo o ambiente necessário para rodar
# a aplicação, incluindo:
# - Instalação do UV (gerenciador de pacotes Python)
# - Criação do ambiente virtual
# - Instalação de dependências
# - Configuração do Supabase
# - Criação de diretórios necessários
# ============================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# ============================================================
# INÍCIO DO SETUP
# ============================================================

clear
echo ""
echo "  ╦  ╦┌─┐┬─┐┌┬┐┬┌─┐┌─┐┬  ┬┌─┐┌─┐   ╔═╗╦"
echo "  ╚╗╔╝├┤ ├┬┘ │ ││  ├─┤│  │┌─┘├─┤───╠═╣║"
echo "   ╚╝ └─┘┴└─ ┴ ┴└─┘┴ ┴┴─┘┴└─┘┴ ┴   ╩ ╩╩"
echo ""
echo "  Sistema de Processamento de Editais com IA"
echo ""

log_header "🚀 SETUP AUTOMATIZADO"

log_info "Este script irá configurar todo o ambiente necessário."
echo ""
read -p "Deseja continuar? (s/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Ss]$ ]]; then
    log_warning "Setup cancelado pelo usuário"
    exit 0
fi

# ============================================================
# 1. VERIFICAR/INSTALAR UV
# ============================================================

log_header "📦 ETAPA 1: UV - Gerenciador de Pacotes Python"

if command -v uv &> /dev/null; then
    UV_VERSION=$(uv --version)
    log_success "UV já instalado: $UV_VERSION"
else
    log_info "Instalando UV..."

    if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh

        # Adicionar ao PATH temporariamente
        export PATH="$HOME/.cargo/bin:$PATH"

        if command -v uv &> /dev/null; then
            log_success "UV instalado com sucesso!"
        else
            log_error "Falha ao instalar UV"
            log_info "Por favor, instale manualmente: https://github.com/astral-sh/uv"
            exit 1
        fi
    else
        log_error "Sistema operacional não suportado para instalação automática de UV"
        log_info "Por favor, instale manualmente: https://github.com/astral-sh/uv"
        exit 1
    fi
fi

# ============================================================
# 2. CRIAR AMBIENTE VIRTUAL
# ============================================================

log_header "🐍 ETAPA 2: Ambiente Virtual Python"

if [ -d ".venv" ]; then
    log_warning "Ambiente virtual já existe"
    read -p "Deseja recriar? (s/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        log_info "Removendo ambiente virtual existente..."
        rm -rf .venv
        log_info "Criando novo ambiente virtual..."
        uv venv
        log_success "Novo ambiente virtual criado"
    else
        log_info "Usando ambiente virtual existente"
    fi
else
    log_info "Criando ambiente virtual..."
    uv venv
    log_success "Ambiente virtual criado em .venv/"
fi

# ============================================================
# 3. INSTALAR DEPENDÊNCIAS
# ============================================================

log_header "📚 ETAPA 3: Instalação de Dependências"

log_info "Instalando dependências Python..."
source .venv/bin/activate
uv pip install -r requirements.txt

log_success "Dependências instaladas (45 pacotes)"

# ============================================================
# 4. CRIAR DIRETÓRIOS NECESSÁRIOS
# ============================================================

log_header "📁 ETAPA 4: Estrutura de Diretórios"

log_info "Criando diretórios necessários..."

mkdir -p input_pdfs
mkdir -p temp
mkdir -p logs

log_success "Diretórios criados: input_pdfs/, temp/, logs/"

# ============================================================
# 5. CONFIGURAR VARIÁVEIS DE AMBIENTE
# ============================================================

log_header "🔐 ETAPA 5: Configuração de Variáveis de Ambiente"

if [ -f ".env" ]; then
    log_warning "Arquivo .env já existe"
    read -p "Deseja reconfigurar? (s/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        log_info "Mantendo .env existente"
        SKIP_ENV_CONFIG=true
    fi
fi

if [ "$SKIP_ENV_CONFIG" != true ]; then
    log_info "Criando arquivo .env a partir do template..."
    cp .env.example .env

    echo ""
    log_info "Configure suas credenciais:"
    echo ""

    read -p "🔑 OpenRouter API Key (obtenha em https://openrouter.ai/keys): " OPENROUTER_KEY

    if [ ! -z "$OPENROUTER_KEY" ]; then
        sed -i.bak "s|OPENROUTER_API_KEY=.*|OPENROUTER_API_KEY=$OPENROUTER_KEY|" .env
        rm -f .env.bak
        log_success "OpenRouter API Key configurada"
    else
        log_warning "OpenRouter API Key não fornecida - configure manualmente no .env"
    fi

    echo ""
    log_info "Modelo LLM primário (padrão: anthropic/claude-3-haiku)"
    read -p "Digite o modelo ou pressione ENTER para usar o padrão: " MODEL_PRIMARY

    if [ ! -z "$MODEL_PRIMARY" ]; then
        sed -i.bak "s|OPENROUTER_MODEL_PRIMARY=.*|OPENROUTER_MODEL_PRIMARY=$MODEL_PRIMARY|" .env
        rm -f .env.bak
    fi
fi

# ============================================================
# 6. CONFIGURAR SUPABASE
# ============================================================

log_header "🗄️  ETAPA 6: Configuração do Supabase"

log_info "O Supabase é necessário para armazenar os dados processados."
echo ""
echo "Escolha uma opção:"
echo "  1) Configurar automaticamente via CLI (requer login)"
echo "  2) Configurar manualmente (você fornece as credenciais)"
echo "  3) Pular (configurar depois)"
echo ""
read -p "Digite sua escolha (1, 2 ou 3): " supabase_choice

case $supabase_choice in
    1)
        log_info "Iniciando configuração automática do Supabase..."
        chmod +x scripts/setup_supabase.sh
        ./scripts/setup_supabase.sh
        ;;
    2)
        echo ""
        read -p "📝 Supabase URL (https://xxxxx.supabase.co): " SUPABASE_URL
        read -p "🔑 Supabase Anon Key: " SUPABASE_KEY

        if [ ! -z "$SUPABASE_URL" ] && [ ! -z "$SUPABASE_KEY" ]; then
            sed -i.bak "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|" .env
            sed -i.bak "s|SUPABASE_KEY=.*|SUPABASE_KEY=$SUPABASE_KEY|" .env
            rm -f .env.bak
            log_success "Credenciais do Supabase configuradas"

            echo ""
            log_warning "IMPORTANTE: Execute o schema SQL no Supabase Dashboard"
            log_info "Arquivo: migrations/001_initial_schema.sql"
            log_info "Dashboard: https://app.supabase.com"
        else
            log_warning "Credenciais não fornecidas - configure manualmente no .env"
        fi
        ;;
    3)
        log_warning "Configuração do Supabase pulada"
        log_info "Configure manualmente editando o arquivo .env"
        log_info "E execute: migrations/001_initial_schema.sql no Supabase Dashboard"
        ;;
    *)
        log_error "Opção inválida"
        ;;
esac

# ============================================================
# 7. VERIFICAÇÃO FINAL
# ============================================================

log_header "🔍 ETAPA 7: Verificação Final"

log_info "Verificando configuração..."

# Verificar .env
if [ -f ".env" ]; then
    log_success "Arquivo .env existe"

    if grep -q "your-key-here" .env || grep -q "your-project.supabase.co" .env; then
        log_warning "Algumas credenciais ainda não foram configuradas no .env"
    fi
else
    log_error "Arquivo .env não encontrado!"
fi

# Verificar ambiente virtual
if [ -d ".venv" ]; then
    log_success "Ambiente virtual configurado"
else
    log_error "Ambiente virtual não encontrado!"
fi

# Verificar diretórios
if [ -d "input_pdfs" ]; then
    log_success "Diretório input_pdfs/ criado"
else
    log_error "Diretório input_pdfs/ não encontrado!"
fi

# ============================================================
# CONCLUSÃO
# ============================================================

log_header "🎉 SETUP CONCLUÍDO!"

echo ""
log_success "Ambiente configurado com sucesso!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 PRÓXIMOS PASSOS:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Verifique o arquivo .env e configure as credenciais faltantes"
echo "   ${YELLOW}nano .env${NC}"
echo ""
echo "2. Se ainda não criou, execute o schema no Supabase:"
echo "   - Acesse: ${BLUE}https://app.supabase.com${NC}"
echo "   - Vá em SQL Editor"
echo "   - Execute: ${YELLOW}migrations/001_initial_schema.sql${NC}"
echo ""
echo "3. Coloque arquivos PDF em:"
echo "   ${YELLOW}input_pdfs/${NC}"
echo ""
echo "4. Execute a aplicação:"
echo "   ${GREEN}source .venv/bin/activate${NC}"
echo "   ${GREEN}python main.py${NC}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Documentação:"
echo "   - README.md - Guia completo"
echo "   - CLAUDE.md - Arquitetura do sistema"
echo "   - migrations/README.md - Guia de migrations"
echo ""
echo "🆘 Suporte:"
echo "   - Issues: https://github.com/seu-usuario/verticaliza-ai/issues"
echo ""
log_success "Pronto para processar editais! 🚀"
echo ""