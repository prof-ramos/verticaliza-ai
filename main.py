from pathlib import Path
import time
import json
import asyncio
from datetime import datetime
from typing import Optional, List

from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.url_handler import URLHandler
from src.processors.llm_client import OpenRouterClient
from src.processors.prompt_templates import build_metadata_prompt, build_verticalization_prompt
from src.database.supabase_client import SupabaseManager
from src.database.models import Edital, Cargo, ConteudoProgramatico, StatusProcessamento
from src.utils.logger import logger
from src.utils.file_hash import compute_file_hash


class EditalProcessor:
    def __init__(self, db: SupabaseManager = None):
        self.db = db or SupabaseManager()
        self.llm_client = OpenRouterClient()

    async def process(
        self,
        pdf_source: str,
        max_pages: Optional[int] = None,
    ) -> bool:
        start_time = time.time()

        # 1. Resolver fonte (local ou URL)
        pdf_path = self._resolve_pdf_source(pdf_source)
        if not pdf_path:
            logger.error("Não foi possível resolver a fonte do PDF")
            return False

        # 2. Calcular hash e verificar duplicata
        file_hash = compute_file_hash(pdf_path)
        edital_existente = await self.db.edital_existe(file_hash)

        if edital_existente:
            logger.info(
                f"✅ Edital já processado (ID: {edital_existente['id']}, "
                f"Hash: {file_hash[:8]}...)"
            )
            return True

        # 3. Criar registro inicial no banco
        edital = Edital(
            hash_arquivo=file_hash,
            nome_arquivo=pdf_path.name,
            url_origem=pdf_source if not Path(pdf_source).exists() else None,
            tamanho_bytes=pdf_path.stat().st_size,
        )

        try:
            edital_id = await self.db.criar_edital(edital)
            logger.info(f"Edital criado no banco: {edital_id}")
        except Exception as e:
            logger.error("Erro ao criar edital no banco", e)
            return False

        try:
            # 4. Extrair texto
            logger.log_extraction_start(pdf_path, "local" if Path(pdf_source).exists() else "url")
            extractor = PDFExtractor(max_pages=max_pages)
            text = extractor.extract_text(pdf_path)
            metadata_basica = extractor.extract_metadata(pdf_path)

            # Atualizar total de páginas
            await self.db.atualizar_edital(edital_id, {
                "total_paginas": metadata_basica["total_pages"],
                "texto_extraido": text  # Armazenar texto completo
            })

            extraction_time = time.time() - start_time
            logger.log_extraction_complete(
                metadata_basica["total_pages"],
                len(text),
                extraction_time
            )

            # 5 e 6. Processar com LLM em paralelo - Metadados e Verticalização
            metadata_prompt = build_metadata_prompt(text[:15000])
            vert_prompt = build_verticalization_prompt(text)

            # Executar ambas chamadas LLM em paralelo
            metadata_task = self.llm_client.process_with_fallback(
                prompt=metadata_prompt,
                system_prompt="Extraia informações precisas do edital em JSON válido."
            )
            vert_task = self.llm_client.process_with_fallback(
                prompt=vert_prompt,
                system_prompt="Estruture o conteúdo mantendo hierarquia original."
            )

            (metadata_json, model_used_meta), (content_md, model_used_vert) = await asyncio.gather(
                metadata_task, vert_task
            )

            logger.log_llm_call(model_used_meta, len(metadata_prompt), len(metadata_json))
            logger.log_llm_call(model_used_vert, len(vert_prompt), len(content_md))

            # 7. Parsear e salvar metadados
            metadata_dict = self._parse_metadata_json(metadata_json)
            await self.db.atualizar_edital(edital_id, {
                "formato_prova": metadata_dict.get("formato_prova"),
                "data_prova": metadata_dict.get("data_prova"),
                "data_inscricao_inicio": metadata_dict.get("data_inscricao_inicio"),
                "data_inscricao_fim": metadata_dict.get("data_inscricao_fim"),
                "valor_inscricao": metadata_dict.get("valor_inscricao"),
                "detalhes_discursiva": metadata_dict.get("detalhes_discursiva"),
                "conteudo_verticalizado_md": content_md,
                "modelo_usado": model_used_vert,
            })

            # 8 e 9. Salvar cargos e conteúdo em paralelo
            cargos = self._parse_cargos(metadata_dict, edital_id)
            conteudos = self._parse_conteudo_programatico(content_md, edital_id)

            await asyncio.gather(
                self.db.inserir_cargos(cargos),
                self.db.inserir_conteudo_programatico(conteudos)
            )

            logger.info(f"Inseridos {len(cargos)} cargos e {len(conteudos)} itens de conteúdo")

            # 10. Finalizar processamento
            tempo_total = time.time() - start_time
            await self.db.finalizar_processamento(
                edital_id=edital_id,
                sucesso=True,
                dados_extras={
                    "tempo_processamento_segundos": round(tempo_total, 2),
                    "custo_total_usd": self.llm_client.total_cost
                }
            )

            logger.info(f"✅ PROCESSAMENTO CONCLUÍDO | ID: {edital_id} | Tempo: {tempo_total:.2f}s")
            return True

        except Exception as e:
            # Marcar como erro no banco
            await self.db.finalizar_processamento(
                edital_id=edital_id,
                sucesso=False,
                erro_mensagem=str(e)
            )
            logger.error("Erro fatal no processamento", e)
            return False

    def _resolve_pdf_source(self, source: str) -> Optional[Path]:
        """Resolve fonte local ou baixa de URL."""
        path = Path(source)
        if path.exists():
            return path

        with URLHandler() as handler:
            output_path = Path("temp") / "edital_baixado.pdf"
            if handler.download_pdf(source, output_path):
                return output_path
        return None

    def _parse_metadata_json(self, metadata_json: str) -> dict:
        """Limpa e parseia JSON retornado pela LLM."""
        import re

        # Remover markdown code blocks
        cleaned = re.sub(r'^```(?:json)?\n?', '', metadata_json.strip())
        cleaned = re.sub(r'\n?```$', '', cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            logger.error(f"JSON inválido: {cleaned[:200]}")
            return {}

    def _parse_cargos(self, metadata_dict: dict, edital_id: str) -> List[Cargo]:
        """Converte metadados em lista de Cargo."""
        cargos = []
        for cargo_nome in metadata_dict.get("cargos", []):
            salario = metadata_dict.get("salarios", {}).get(cargo_nome)
            cargos.append(Cargo(
                edital_id=edital_id,
                nome=cargo_nome,
                salario=salario
            ))
        return cargos

    def _parse_conteudo_programatico(
        self,
        markdown_content: str,
        edital_id: str
    ) -> List[ConteudoProgramatico]:
        """Parseia markdown em estrutura hierárquica."""
        import re

        lines = markdown_content.split('\n')
        conteudos = []
        current_section = None
        current_materia = None
        ordem = 0

        for line in lines:
            line = line.strip()

            if line.startswith('## '):
                current_section = line[3:].strip()
                continue

            if line.startswith('### '):
                current_materia = line[4:].strip().upper()
                continue

            if not line or line.startswith('#') or line.startswith('---'):
                continue

            # Parsear numeração hierárquica
            patterns = [
                r'^(\d+(?:\.\d+)*)[.\)]\s+(.+)$',
                r'^(\d+(?:\.\d+)*)\s*[-–—]\s*(.+)$',
                r'^(\d+(?:\.\d+)*)\s+([A-ZÀ-Ú].+)$',
            ]

            matched = False
            for pattern in patterns:
                match = re.match(pattern, line)
                if match:
                    numeracao, descricao = match.groups()
                    partes = numeracao.split('.')

                    conteudos.append(ConteudoProgramatico(
                        edital_id=edital_id,
                        secao=current_section,
                        materia=current_materia,
                        descricao=descricao.strip(),
                        nivel_1=partes[0] if len(partes) >= 1 else None,
                        nivel_2=partes[1] if len(partes) >= 2 else None,
                        nivel_3=partes[2] if len(partes) >= 3 else None,
                        nivel_4=partes[3] if len(partes) >= 4 else None,
                        ordem=ordem
                    ))
                    ordem += 1
                    matched = True
                    break

            # Se não houver numeração, adicionar como item simples
            if not matched and line:
                clean_line = re.sub(r'^\s*[-•]\s*', '', line).strip()
                if clean_line:
                    conteudos.append(ConteudoProgramatico(
                        edital_id=edital_id,
                        secao=current_section,
                        materia=current_materia,
                        descricao=clean_line,
                        ordem=ordem
                    ))
                    ordem += 1

        return conteudos


async def process_pdf_with_info(processor: EditalProcessor, pdf_file: Path) -> dict:
    """Processa um PDF e retorna informações do resultado."""
    print(f"\n{'='*60}")
    print(f"🔄 Processando: {pdf_file.name}")
    print(f"{'='*60}\n")

    success = await processor.process(
        pdf_source=str(pdf_file),
        max_pages=None  # Processar todas as páginas
    )

    return {
        'arquivo': pdf_file.name,
        'sucesso': success
    }


async def main():
    """Função principal com processamento paralelo de PDFs."""
    processor = EditalProcessor()

    # Verificar se há PDFs no diretório input_pdfs
    input_dir = Path("input_pdfs")
    pdf_files = list(input_dir.glob("*.pdf")) if input_dir.exists() else []

    if not pdf_files:
        print("❌ Nenhum PDF encontrado no diretório 'input_pdfs/'")
        print("\n💡 Dica: Coloque arquivos PDF no diretório 'input_pdfs/' ou forneça uma URL\n")
        print("Exemplo de uso programático:")
        print("  await processor.process('input_pdfs/edital.pdf')")
        print("  await processor.process('https://exemplo.com/edital.pdf')")
        exit(1)

    print(f"📂 Encontrados {len(pdf_files)} PDF(s) no diretório 'input_pdfs/'")
    print(f"⚡ Processamento paralelo habilitado\n")

    # Processar todos os PDFs em paralelo (máximo 3 simultâneos para não sobrecarregar)
    max_concurrent = 3
    resultados = []

    for i in range(0, len(pdf_files), max_concurrent):
        batch = pdf_files[i:i + max_concurrent]
        batch_results = await asyncio.gather(
            *[process_pdf_with_info(processor, pdf) for pdf in batch],
            return_exceptions=True
        )

        # Processar resultados do batch
        for result in batch_results:
            if isinstance(result, Exception):
                print(f"❌ Erro: {result}")
                resultados.append({'arquivo': 'desconhecido', 'sucesso': False})
            else:
                resultados.append(result)

    # Mostrar resumo
    print(f"\n\n{'='*60}")
    print("📊 RESUMO DO PROCESSAMENTO")
    print(f"{'='*60}\n")

    for resultado in resultados:
        status = "✅ Sucesso" if resultado['sucesso'] else "❌ Falha"
        print(f"  {status} - {resultado['arquivo']}")

    # Mostrar estatísticas gerais
    stats = await processor.db.estatisticas_processamento()
    print(f"\n📈 Estatísticas Gerais:")
    print(f"  Total de editais: {stats['total_editais']}")
    print(f"  Concluídos: {stats['concluidos']}")
    print(f"  Erros: {stats['erros']}")
    print(f"  Custo total: US$ {stats['custo_total_usd']:.2f}")

    # Mostrar estatísticas de cache LLM
    cache_stats = processor.llm_client.get_cache_stats()
    if not cache_stats.get("cache_disabled"):
        print(f"\n💾 Cache LLM:")
        print(f"  Hits: {cache_stats['hits']}")
        print(f"  Misses: {cache_stats['misses']}")
        print(f"  Taxa de acerto: {cache_stats['hit_rate_percent']:.2f}%")
        print(f"  Tamanho: {cache_stats['cache_size']} entradas\n")

    # Fechar conexões
    await processor.db.close()


if __name__ == "__main__":
    asyncio.run(main())