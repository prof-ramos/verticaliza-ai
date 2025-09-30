import os
from typing import Optional, List, Dict, Any
import httpx
from dotenv import load_dotenv

from .models import Edital, Cargo, ConteudoProgramatico, StatusProcessamento

load_dotenv()

class SupabaseManager:
    def __init__(self, pool_size: int = 10, max_keepalive: int = 5):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env")

        self.base_url = url
        self.api_key = key
        self.rest_url = f"{url}/rest/v1"

        # Cliente HTTP assíncrono com connection pooling
        self.client = httpx.AsyncClient(
            base_url=self.rest_url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
                "Prefer": "return=representation"
            },
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=pool_size,
                max_keepalive_connections=max_keepalive
            )
        )

    async def close(self):
        """Fecha conexões HTTP."""
        await self.client.aclose()

    # ==================== EDITAIS ====================

    async def edital_existe(self, hash_arquivo: str) -> Optional[Dict[str, Any]]:
        """Verifica se edital já foi processado pelo hash."""
        response = await self.client.get(
            "/editais",
            params={"hash_arquivo": f"eq.{hash_arquivo}", "select": "*"}
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if data else None

    async def criar_edital(self, edital: Edital) -> str:
        """Cria registro de edital e retorna o ID."""
        data = {
            "hash_arquivo": edital.hash_arquivo,
            "nome_arquivo": edital.nome_arquivo,
            "url_origem": edital.url_origem,
            "tamanho_bytes": edital.tamanho_bytes,
            "total_paginas": edital.total_paginas,
            "status": edital.status.value,
        }

        response = await self.client.post("/editais", json=data)
        response.raise_for_status()
        result = response.json()
        return result[0]["id"]

    async def atualizar_edital(
        self,
        edital_id: str,
        dados: Dict[str, Any]
    ) -> bool:
        """Atualiza campos do edital."""
        try:
            response = await self.client.patch(
                f"/editais?id=eq.{edital_id}",
                json=dados
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Erro ao atualizar edital: {e}")
            return False

    async def finalizar_processamento(
        self,
        edital_id: str,
        sucesso: bool,
        erro_mensagem: Optional[str] = None,
        dados_extras: Optional[Dict[str, Any]] = None
    ):
        """Marca edital como concluído ou com erro."""
        from datetime import datetime

        update_data = {
            "status": StatusProcessamento.CONCLUIDO.value if sucesso else StatusProcessamento.ERRO.value,
            "data_processamento": datetime.utcnow().isoformat(),
        }

        if erro_mensagem:
            update_data["erro_mensagem"] = erro_mensagem

        if dados_extras:
            update_data.update(dados_extras)

        return await self.atualizar_edital(edital_id, update_data)

    # ==================== CARGOS ====================

    async def inserir_cargos(self, cargos: List[Cargo]) -> bool:
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
            response = await self.client.post("/cargos", json=data)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Erro ao inserir cargos: {e}")
            return False

    # ==================== CONTEÚDO PROGRAMÁTICO ====================

    async def inserir_conteudo_programatico(
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
                response = await self.client.post("/conteudo_programatico", json=data)
                response.raise_for_status()

            return True
        except Exception as e:
            print(f"Erro ao inserir conteúdo programático: {e}")
            return False

    # ==================== CONSULTAS ====================

    async def buscar_editais_recentes(self, limite: int = 10) -> List[Dict[str, Any]]:
        """Retorna editais processados recentemente."""
        response = await self.client.get(
            "/editais",
            params={
                "status": f"eq.{StatusProcessamento.CONCLUIDO.value}",
                "select": "*",
                "order": "data_processamento.desc",
                "limit": limite
            }
        )
        response.raise_for_status()
        return response.json()

    async def buscar_conteudo_por_materia(
        self,
        edital_id: str,
        materia: str
    ) -> List[Dict[str, Any]]:
        """Busca tópicos de uma matéria específica."""
        response = await self.client.get(
            "/conteudo_programatico",
            params={
                "edital_id": f"eq.{edital_id}",
                "materia": f"ilike.*{materia}*",
                "select": "*",
                "order": "ordem"
            }
        )
        response.raise_for_status()
        return response.json()

    async def estatisticas_processamento(self) -> Dict[str, Any]:
        """Retorna estatísticas gerais."""
        # Total de editais
        total_resp = await self.client.get(
            "/editais",
            params={"select": "id"},
            headers={"Prefer": "count=exact"}
        )
        total = int(total_resp.headers.get("Content-Range", "0-0/0").split("/")[1])

        # Concluídos
        concluidos_resp = await self.client.get(
            "/editais",
            params={
                "status": f"eq.{StatusProcessamento.CONCLUIDO.value}",
                "select": "id"
            },
            headers={"Prefer": "count=exact"}
        )
        concluidos = int(concluidos_resp.headers.get("Content-Range", "0-0/0").split("/")[1])

        # Erros
        erros_resp = await self.client.get(
            "/editais",
            params={
                "status": f"eq.{StatusProcessamento.ERRO.value}",
                "select": "id"
            },
            headers={"Prefer": "count=exact"}
        )
        erros = int(erros_resp.headers.get("Content-Range", "0-0/0").split("/")[1])

        # Custo total
        custos_resp = await self.client.get(
            "/editais",
            params={"select": "custo_total_usd"}
        )
        custos_data = custos_resp.json()
        custo_total = sum(
            float(c.get("custo_total_usd") or 0)
            for c in custos_data
        )

        return {
            "total_editais": total,
            "concluidos": concluidos,
            "erros": erros,
            "custo_total_usd": round(custo_total, 2)
        }
