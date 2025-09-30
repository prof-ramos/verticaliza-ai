-- Migration: Initial Schema
-- Descrição: Cria estrutura inicial para processamento de editais
-- Data: 2025-09-30

-- ============================================================
-- TABELA: editais
-- ============================================================
CREATE TABLE IF NOT EXISTS editais (
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

-- ============================================================
-- TABELA: cargos
-- ============================================================
CREATE TABLE IF NOT EXISTS cargos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edital_id UUID REFERENCES editais(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    salario TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- TABELA: conteudo_programatico
-- ============================================================
CREATE TABLE IF NOT EXISTS conteudo_programatico (
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

-- ============================================================
-- ÍNDICES PARA PERFORMANCE
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_editais_hash ON editais(hash_arquivo);
CREATE INDEX IF NOT EXISTS idx_editais_status ON editais(status);
CREATE INDEX IF NOT EXISTS idx_cargos_edital ON cargos(edital_id);
CREATE INDEX IF NOT EXISTS idx_conteudo_edital ON conteudo_programatico(edital_id);
CREATE INDEX IF NOT EXISTS idx_conteudo_materia ON conteudo_programatico(materia);

-- ============================================================
-- COMENTÁRIOS DAS TABELAS
-- ============================================================
COMMENT ON TABLE editais IS 'Armazena informações principais dos editais processados';
COMMENT ON TABLE cargos IS 'Cargos e salários vinculados a cada edital';
COMMENT ON TABLE conteudo_programatico IS 'Estrutura hierárquica do conteúdo programático';

-- ============================================================
-- COMENTÁRIOS DAS COLUNAS PRINCIPAIS
-- ============================================================
COMMENT ON COLUMN editais.hash_arquivo IS 'Hash SHA-256 do arquivo para deduplicação';
COMMENT ON COLUMN editais.status IS 'Status: processando, concluido, erro';
COMMENT ON COLUMN editais.texto_extraido IS 'Texto completo extraído do PDF';
COMMENT ON COLUMN editais.conteudo_verticalizado_md IS 'Conteúdo estruturado em Markdown pela LLM';
COMMENT ON COLUMN conteudo_programatico.nivel_1 IS 'Primeiro nível da hierarquia (ex: 1)';
COMMENT ON COLUMN conteudo_programatico.nivel_2 IS 'Segundo nível da hierarquia (ex: 1.1)';
COMMENT ON COLUMN conteudo_programatico.nivel_3 IS 'Terceiro nível da hierarquia (ex: 1.1.1)';
COMMENT ON COLUMN conteudo_programatico.nivel_4 IS 'Quarto nível da hierarquia (ex: 1.1.1.1)';
COMMENT ON COLUMN conteudo_programatico.ordem IS 'Ordem sequencial dos itens no documento';