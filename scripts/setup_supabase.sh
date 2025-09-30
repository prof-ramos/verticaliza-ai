#!/bin/bash

# Script para configurar o Supabase automaticamente
# Uso: ./scripts/setup_supabase.sh

set -e

echo "🔧 Configurando Supabase para Verticaliza-AI..."
echo ""

# Verificar se o CLI do Supabase está instalado
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI não encontrado!"
    echo ""
    echo "Instalando Supabase CLI..."

    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install supabase/tap/supabase
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        brew install supabase/tap/supabase
    else
        echo "❌ Sistema operacional não suportado para instalação automática"
        echo "Por favor, instale manualmente: https://supabase.com/docs/guides/cli"
        exit 1
    fi
fi

echo "✅ Supabase CLI instalado"
echo ""

# Verificar se já está logado
if ! supabase projects list &> /dev/null; then
    echo "🔐 Fazendo login no Supabase..."
    echo "Uma janela do navegador será aberta para autenticação."
    supabase login
else
    echo "✅ Já autenticado no Supabase"
fi

echo ""
echo "📋 Listando seus projetos Supabase..."
echo ""

supabase projects list

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 CONFIGURAÇÃO DO PROJETO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Escolha uma opção:"
echo "  1) Usar um projeto existente"
echo "  2) Criar um novo projeto"
echo ""
read -p "Digite sua escolha (1 ou 2): " choice

if [ "$choice" == "2" ]; then
    echo ""
    read -p "📝 Nome do projeto: " project_name
    read -p "🔐 Senha do banco de dados (mínimo 12 caracteres): " db_password
    read -p "🌍 Região (us-east-1, eu-central-1, etc): " region

    echo ""
    echo "Criando projeto '$project_name'..."
    supabase projects create "$project_name" \
        --db-password "$db_password" \
        --region "$region" \
        --org-id "$(supabase orgs list | grep -v 'ID' | head -1 | awk '{print $1}')"

    # Aguardar criação do projeto
    echo "⏳ Aguardando projeto ser criado (isso pode levar alguns minutos)..."
    sleep 30

    PROJECT_REF=$(supabase projects list | grep "$project_name" | awk '{print $3}')
else
    echo ""
    read -p "📝 Digite o Project Reference ID: " PROJECT_REF
fi

echo ""
echo "🔗 Vinculando projeto local ao Supabase..."
supabase link --project-ref "$PROJECT_REF"

echo ""
echo "📊 Aplicando schema do banco de dados..."
supabase db push --db-url "$(supabase projects api-keys --project-ref $PROJECT_REF | grep 'DB URL' | awk '{print $3}')" < migrations/001_initial_schema.sql || {
    echo "⚠️  Falha ao aplicar via CLI, tentando método alternativo..."
    echo ""
    echo "Por favor, execute manualmente no SQL Editor do Supabase:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat migrations/001_initial_schema.sql
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    read -p "Pressione ENTER após executar o SQL no Supabase Dashboard..."
}

echo ""
echo "🔑 Obtendo credenciais do projeto..."
API_KEYS=$(supabase projects api-keys --project-ref "$PROJECT_REF")

SUPABASE_URL=$(echo "$API_KEYS" | grep "API URL" | awk '{print $3}')
SUPABASE_ANON_KEY=$(echo "$API_KEYS" | grep "anon key" | awk '{print $3}')

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ SUPABASE CONFIGURADO COM SUCESSO!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📝 Credenciais obtidas:"
echo "   URL: $SUPABASE_URL"
echo "   Anon Key: ${SUPABASE_ANON_KEY:0:20}..."
echo ""
echo "💾 Salvando no arquivo .env..."

# Atualizar .env se existir, ou criar novo
if [ -f .env ]; then
    sed -i.bak "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|" .env
    sed -i.bak "s|SUPABASE_KEY=.*|SUPABASE_KEY=$SUPABASE_ANON_KEY|" .env
    rm .env.bak
    echo "✅ Arquivo .env atualizado"
else
    cp .env.example .env
    sed -i.bak "s|SUPABASE_URL=.*|SUPABASE_URL=$SUPABASE_URL|" .env
    sed -i.bak "s|SUPABASE_KEY=.*|SUPABASE_KEY=$SUPABASE_ANON_KEY|" .env
    rm .env.bak
    echo "✅ Arquivo .env criado"
fi

echo ""
echo "🎉 Configuração do Supabase concluída!"
echo ""
echo "⚠️  IMPORTANTE: Configure sua OPENROUTER_API_KEY no arquivo .env"
echo "   Obtenha sua chave em: https://openrouter.ai/keys"
echo ""