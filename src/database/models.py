from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class StatusProcessamento(str, Enum):
    PROCESSANDO = "processando"
    CONCLUIDO = "concluido"
    ERRO = "erro"

@dataclass
class Edital:
    hash_arquivo: str
    nome_arquivo: str
    url_origem: Optional[str] = None
    tamanho_bytes: Optional[int] = None
    total_paginas: Optional[int] = None
    status: StatusProcessamento = StatusProcessamento.PROCESSANDO
    erro_mensagem: Optional[str] = None
    data_upload: datetime = None
    data_processamento: Optional[datetime] = None
    tempo_processamento_segundos: Optional[float] = None
    custo_total_usd: Optional[float] = None
    modelo_usado: Optional[str] = None
    formato_prova: Optional[str] = None
    data_prova: Optional[date] = None
    data_inscricao_inicio: Optional[date] = None
    data_inscricao_fim: Optional[date] = None
    valor_inscricao: Optional[str] = None
    detalhes_discursiva: Optional[str] = None
    texto_extraido: Optional[str] = None
    conteudo_verticalizado_md: Optional[str] = None
    id: Optional[str] = None

@dataclass
class Cargo:
    edital_id: str
    nome: str
    salario: Optional[str] = None
    id: Optional[str] = None

@dataclass
class ConteudoProgramatico:
    edital_id: str
    descricao: str
    secao: Optional[str] = None
    materia: Optional[str] = None
    nivel_1: Optional[str] = None
    nivel_2: Optional[str] = None
    nivel_3: Optional[str] = None
    nivel_4: Optional[str] = None
    ordem: Optional[int] = None
    id: Optional[str] = None