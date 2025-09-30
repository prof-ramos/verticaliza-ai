import os
from typing import Optional, List, Dict, Any
from supabase import create_client
from supabase.client import Client
from dotenv import load_dotenv

from .models import Edital, Cargo, ConteudoProgramatico, StatusProcessamento

load_dotenv()

class SupabaseManager:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env")

        self.client: Client = create_client(url, key)

    # ==================== EDITAIS ====================

    def edital_existe(self, hash_arquivo: str) -> Optional[Dict[str, Any]]:
        """Verifica se edital já foi processado pelo hash."""
        response = self.client.table("editais")\
            .select("*")\
            .eq("hash_arquivo", hash_arquivo)\
            .execute()

        return response.data[0] if response.data else None

    def criar_edital(self, edital: Edital) -> str:
        """Cria registro de edital e retorna o ID."""
        data = {
            "hash_arquivo": edital.hash_arquivo,
            "nome_arquivo": edital.nome_arquivo,
            "url_origem": edital.url_origem,
            "tamanho_bytes": edital.tamanho_bytes,
            "total_paginas": edital.total_paginas,
            "status": edital.status.value,
        }

        response = self.client.table("editais").insert(data).execute()
        return response.data[0]["id"]

    def atualizar_edital(
        self,
        edital_id: str,
        dados: Dict[str, Any]
    ) -> bool:
        """Atualiza campos do edital."""
        try:
            self.client.table("editais")\
                .update(dados)\
                .eq("id", edital_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Erro ao atualizar edital: {e}")
            return False

    def finalizar_processamento(
        self,
        edital_id: str,
        sucesso: bool,
        erro_mensagem: Optional[str] = None,
        dados_extras: Optional[Dict[str, Any]] = None
    ):
        """Marca edital como concluído ou com erro."""
        update_data = {
            "status": StatusProcessamento.CONCLUIDO.value if sucesso else StatusProcessamento.ERRO.value,
            "data_processamento": "now()",
        }

        if erro_mensagem:
            update_data["erro_mensagem"] = erro_mensagem

        if dados_extras:
            update_data.update(dados_extras)

        return self.atualizar_edital(edital_id, update_data)

    # ==================== CARGOS ====================

    def inserir_cargos(self, cargos: List[Cargo]) -> bool:
        """Insere múltiplos cargos de uma vez."""
        if not cargos:
            return True

        data = [
            {
                "edital_id": cargo.edital_id,
                "nome": cargo.nome,
                "salario": cargo.salario
            }
            for cargo in cargos
        ]

        try:
            self.client.table("cargos").insert(data).execute()
            return True
        except Exception as e:
            print(f"Erro ao inserir cargos: {e}")
            return False

    # ==================== CONTEÚDO PROGRAMÁTICO ====================

    def inserir_conteudo_programatico(
        self,
        conteudos: List[ConteudoProgramatico],
        batch_size: int = 100
    ) -> bool:
        """Insere conteúdo programático em lotes."""
        if not conteudos:
            return True

        try:
            # Processar em batches para evitar timeouts
            for i in range(0, len(conteudos), batch_size):
                batch = conteudos[i:i + batch_size]
                data = [
                    {
                        "edital_id": c.edital_id,
                        "secao": c.secao,
                        "materia": c.materia,
                        "descricao": c.descricao,
                        "nivel_1": c.nivel_1,
                        "nivel_2": c.nivel_2,
                        "nivel_3": c.nivel_3,
                        "nivel_4": c.nivel_4,
                        "ordem": c.ordem
                    }
                    for c in batch
                ]
                self.client.table("conteudo_programatico").insert(data).execute()

            return True
        except Exception as e:
            print(f"Erro ao inserir conteúdo programático: {e}")
            return False

    # ==================== CONSULTAS ====================

    def buscar_editais_recentes(self, limite: int = 10) -> List[Dict[str, Any]]:
        """Retorna editais processados recentemente."""
        response = self.client.table("editais")\
            .select("*")\
            .eq("status", StatusProcessamento.CONCLUIDO.value)\
            .order("data_processamento", desc=True)\
            .limit(limite)\
            .execute()

        return response.data

    def buscar_conteudo_por_materia(
        self,
        edital_id: str,
        materia: str
    ) -> List[Dict[str, Any]]:
        """Busca tópicos de uma matéria específica."""
        response = self.client.table("conteudo_programatico")\
            .select("*")\
            .eq("edital_id", edital_id)\
            .ilike("materia", f"%{materia}%")\
            .order("ordem")\
            .execute()

        return response.data

    def estatisticas_processamento(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais."""
        # Total de editais
        total = self.client.table("editais").select("id", count="exact").execute()

        # Por status
        concluidos = self.client.table("editais")\
            .select("id", count="exact")\
            .eq("status", StatusProcessamento.CONCLUIDO.value)\
            .execute()

        erros = self.client.table("editais")\
            .select("id", count="exact")\
            .eq("status", StatusProcessamento.ERRO.value)\
            .execute()

        # Custo total
        custos = self.client.table("editais")\
            .select("custo_total_usd")\
            .execute()

        custo_total = sum(
            float(c["custo_total_usd"] or 0)
            for c in custos.data
        )

        return {
            "total_editais": total.count,
            "concluidos": concluidos.count,
            "erros": erros.count,
            "custo_total_usd": round(custo_total, 2)
        }
