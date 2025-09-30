"""
Script de teste para demonstrar as otimizações implementadas.
Este script mostra como usar o sistema com todas as melhorias de performance.
"""
import asyncio
import time
from pathlib import Path
from main import EditalProcessor


async def test_single_pdf():
    """Testa processamento de um único PDF."""
    print("=" * 60)
    print("TESTE 1: Processamento de um único PDF")
    print("=" * 60)

    processor = EditalProcessor()
    start = time.time()

    # Substitua pelo caminho de um PDF real
    test_pdf = "input_pdfs/exemplo.pdf"

    if not Path(test_pdf).exists():
        print(f"⚠️  PDF de teste não encontrado: {test_pdf}")
        print("   Crie o diretório 'input_pdfs/' e adicione um PDF para testar\n")
        return

    success = await processor.process(test_pdf)

    elapsed = time.time() - start
    print(f"\n{'✅' if success else '❌'} Processamento {'concluído' if success else 'falhou'}")
    print(f"⏱️  Tempo total: {elapsed:.2f}s")

    # Mostrar estatísticas de cache
    cache_stats = processor.llm_client.get_cache_stats()
    print(f"\n💾 Cache LLM:")
    print(f"   Hits: {cache_stats.get('hits', 0)}")
    print(f"   Misses: {cache_stats.get('misses', 0)}")

    await processor.db.close()


async def test_parallel_processing():
    """Testa processamento paralelo de múltiplos PDFs."""
    print("\n" + "=" * 60)
    print("TESTE 2: Processamento paralelo de múltiplos PDFs")
    print("=" * 60)

    input_dir = Path("input_pdfs")
    if not input_dir.exists():
        print("⚠️  Diretório 'input_pdfs/' não encontrado")
        return

    pdf_files = list(input_dir.glob("*.pdf"))
    if len(pdf_files) < 2:
        print(f"⚠️  Apenas {len(pdf_files)} PDF(s) encontrado(s)")
        print("   Adicione pelo menos 2 PDFs para testar processamento paralelo\n")
        return

    processor = EditalProcessor()

    # Teste sequencial (simulado)
    print(f"\n📂 Encontrados {len(pdf_files)} PDFs")
    print("\n🐌 Simulando processamento SEQUENCIAL...")
    start_seq = time.time()

    # Na verdade vamos processar em paralelo, mas calcular o tempo estimado sequencial
    results = []
    times = []

    for pdf_file in pdf_files[:3]:  # Limitar a 3 para o teste
        start = time.time()
        success = await processor.process(str(pdf_file))
        elapsed = time.time() - start
        times.append(elapsed)
        results.append(success)

    tempo_sequencial = sum(times)
    print(f"   Tempo sequencial (estimado): {tempo_sequencial:.2f}s")

    # Agora processar em paralelo (de verdade)
    print("\n⚡ Processamento PARALELO...")
    start_par = time.time()

    tasks = [processor.process(str(pdf)) for pdf in pdf_files[:3]]
    results_parallel = await asyncio.gather(*tasks, return_exceptions=True)

    tempo_paralelo = time.time() - start_par
    print(f"   Tempo paralelo: {tempo_paralelo:.2f}s")

    # Calcular ganho
    speedup = tempo_sequencial / tempo_paralelo if tempo_paralelo > 0 else 0
    economia = ((tempo_sequencial - tempo_paralelo) / tempo_sequencial * 100) if tempo_sequencial > 0 else 0

    print(f"\n📊 COMPARAÇÃO:")
    print(f"   Speedup: {speedup:.2f}x mais rápido")
    print(f"   Economia de tempo: {economia:.1f}%")

    # Estatísticas de cache
    cache_stats = processor.llm_client.get_cache_stats()
    if cache_stats.get('hits', 0) > 0:
        print(f"\n💾 Cache LLM salvou:")
        print(f"   {cache_stats['hits']} chamadas (${cache_stats['hits'] * 0.01:.2f} USD estimado)")

    await processor.db.close()


async def test_cache_effectiveness():
    """Testa efetividade do cache processando o mesmo PDF duas vezes."""
    print("\n" + "=" * 60)
    print("TESTE 3: Efetividade do cache LLM")
    print("=" * 60)

    test_pdf = "input_pdfs/exemplo.pdf"
    if not Path(test_pdf).exists():
        print(f"⚠️  PDF de teste não encontrado: {test_pdf}\n")
        return

    processor = EditalProcessor()

    # Primeira execução (sem cache)
    print("\n🔄 Primeira execução (SEM cache)...")
    start1 = time.time()
    await processor.process(test_pdf)
    time1 = time.time() - start1

    stats1 = processor.llm_client.get_cache_stats()
    print(f"   Tempo: {time1:.2f}s")
    print(f"   Cache misses: {stats1['misses']}")

    # Segunda execução (com cache)
    print("\n🔄 Segunda execução (COM cache)...")
    start2 = time.time()
    await processor.process(test_pdf)
    time2 = time.time() - start2

    stats2 = processor.llm_client.get_cache_stats()
    print(f"   Tempo: {time2:.2f}s")
    print(f"   Cache hits: {stats2['hits'] - stats1.get('hits', 0)}")

    # Comparação
    if time1 > 0:
        speedup = time1 / time2 if time2 > 0 else float('inf')
        economia = ((time1 - time2) / time1 * 100) if time1 > 0 else 0

        print(f"\n📊 GANHO DO CACHE:")
        print(f"   {speedup:.2f}x mais rápido")
        print(f"   Economia de tempo: {economia:.1f}%")
        print(f"   Economia de custo: ~${(stats2['hits'] - stats1.get('hits', 0)) * 0.01:.2f} USD")

    await processor.db.close()


async def main():
    """Executa todos os testes."""
    print("\n🚀 TESTES DE OTIMIZAÇÕES DE PERFORMANCE")
    print("=" * 60)

    try:
        await test_single_pdf()
        await test_parallel_processing()
        await test_cache_effectiveness()

        print("\n" + "=" * 60)
        print("✅ TESTES CONCLUÍDOS")
        print("=" * 60)
        print("\nPara mais informações, veja: PERFORMANCE_OPTIMIZATIONS.md\n")

    except Exception as e:
        print(f"\n❌ Erro durante testes: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())