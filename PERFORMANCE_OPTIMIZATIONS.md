# Otimizações de Performance

Este documento detalha as otimizações implementadas no sistema de processamento de editais.

## Resumo das Otimizações

1. ✅ **Processamento Paralelo de Múltiplos PDFs**
2. ✅ **Batch Inserts no Supabase**
3. ✅ **Cache de Resultados LLM**
4. ✅ **Async I/O para Chamadas LLM e DB**
5. ✅ **Connection Pooling no Supabase**

---

## 1. Processamento Paralelo de Múltiplos PDFs

### Implementação
- **Arquivo**: `main.py:298-315`
- **Estratégia**: Processamento em batches de até 3 PDFs simultâneos usando `asyncio.gather()`
- **Benefício**: Reduz tempo total ao processar múltiplos editais

### Configuração
```python
max_concurrent = 3  # Ajuste conforme recursos disponíveis
```

### Ganho Estimado
- **3 PDFs**: ~70% mais rápido (tempo/3 vs tempo*3)
- **10 PDFs**: ~65% mais rápido

---

## 2. Batch Inserts no Supabase

### Implementação
- **Arquivo**: `src/database/supabase_client.py:136-169`
- **Estratégia**: Inserção em lotes de 100 registros por vez
- **Benefício**: Reduz latência de rede e overhead de conexões HTTP

### Configuração
```python
await db.inserir_conteudo_programatico(conteudos, batch_size=100)
```

### Ganho Estimado
- **1000 registros**: ~90% mais rápido (10 requests vs 1000)
- **5000 registros**: ~98% mais rápido (50 requests vs 5000)

---

## 3. Cache de Resultados LLM

### Implementação
- **Arquivo**: `src/utils/llm_cache.py`
- **Estratégia**: Cache persistente em disco usando `diskcache` com TTL de 24h
- **Chave**: Hash SHA-256 de `{modelo}|{system_prompt}|{prompt}`
- **Benefício**: Evita chamadas duplicadas à LLM (custo e latência)

### Configuração
```python
# Habilitar/desabilitar cache
llm_client = OpenRouterClient(cache_enabled=True, cache_ttl=86400)

# Limpar cache
llm_client.cache.clear()

# Ver estatísticas
stats = llm_client.get_cache_stats()
```

### Diretório de Cache
```
.cache/llm/  # Cache persistente entre execuções
```

### Ganho Estimado
- **Edital duplicado**: ~100% economia (sem custo LLM)
- **Reprocessamento**: Até 95% mais rápido

---

## 4. Async I/O para LLM e DB

### Implementação

#### LLM Client (`src/processors/llm_client.py`)
- Usa `AsyncOpenAI` da biblioteca openai
- Timeout configurado: 60s
- Max retries: 2

#### Supabase Client (`src/database/supabase_client.py`)
- Usa `httpx.AsyncClient` para chamadas REST assíncronas
- Todas as operações convertidas para async/await

#### EditalProcessor (`main.py:23-149`)
- Método `process()` convertido para async
- **Paralelização interna**: Chamadas LLM de metadados e verticalização executam em paralelo (linha 96)
- **Paralelização de inserts**: Cargos e conteúdo programático inseridos em paralelo (linha 120)

### Benefício
- Chamadas LLM executam simultaneamente (economia de ~50% no tempo de LLM)
- Inserts no banco executam simultaneamente
- CPU não fica bloqueada esperando I/O

### Ganho Estimado
- **Chamadas LLM paralelas**: ~40-50% mais rápido por edital
- **Inserts paralelos**: ~30% mais rápido

---

## 5. Connection Pooling no Supabase

### Implementação
- **Arquivo**: `src/database/supabase_client.py:23-36`
- **Cliente**: `httpx.AsyncClient` com limits configurados

### Configuração
```python
SupabaseManager(
    pool_size=10,           # Máximo de conexões simultâneas
    max_keepalive=5         # Conexões mantidas vivas
)
```

### Benefício
- Reutiliza conexões HTTP
- Reduz overhead de handshake TCP/TLS
- Melhora throughput em operações batch

### Ganho Estimado
- **Múltiplas requisições**: ~20-30% mais rápido
- **Batch operations**: ~15% mais rápido

---

## Ganhos Totais Estimados

### Cenário 1: Processamento de 1 edital
- Chamadas LLM paralelas: **-40%**
- Cache (reprocessamento): **-95%**
- Connection pooling: **-15%**
- **Total**: ~50-60% mais rápido (primeiro processamento)
- **Total (reprocessamento)**: ~95% mais rápido

### Cenário 2: Processamento de 10 editais
- Processamento paralelo (3x): **-65%**
- Async I/O: **-40%**
- Batch inserts: **-90%**
- Connection pooling: **-20%**
- **Total**: ~70-80% mais rápido

### Economia de Custos
- Cache LLM evita chamadas duplicadas
- **Hit rate de 30%**: ~30% de economia em custos de LLM
- **Hit rate de 70%**: ~70% de economia

---

## Monitoramento de Performance

### Estatísticas de Cache
Execute o sistema e veja as estatísticas ao final:

```
💾 Cache LLM:
  Hits: 15
  Misses: 5
  Taxa de acerto: 75.00%
  Tamanho: 20 entradas
```

### Logs de Tempo
O sistema registra automaticamente:
- Tempo de extração de PDF
- Tempo de chamadas LLM
- Tempo total de processamento

---

## Configurações Recomendadas

### Para Desenvolvimento Local
```python
max_concurrent = 2          # Não sobrecarregar CPU local
pool_size = 5              # Conexões moderadas
cache_ttl = 3600           # 1h (testes rápidos)
```

### Para Produção
```python
max_concurrent = 5          # Aproveitar recursos do servidor
pool_size = 20             # Maior throughput
cache_ttl = 86400          # 24h (economia máxima)
```

### Para Processamento em Massa
```python
max_concurrent = 10         # Máxima paralelização
pool_size = 30             # Alta concorrência
batch_size = 200           # Batches maiores
```

---

## Próximos Passos (Futuras Otimizações)

1. **Cálculo real de custo por modelo**: Implementar tracking preciso baseado em tokens
2. **Rate limiting inteligente**: Respeitar limites de API do OpenRouter
3. **Métricas detalhadas**: Adicionar OpenTelemetry para observabilidade
4. **Compressão de texto**: Comprimir texto extraído antes de enviar para LLM
5. **Streaming de respostas LLM**: Processar resposta enquanto ainda está sendo gerada
6. **Pool de workers**: Distribuir processamento entre múltiplos processos Python

---

## Dependências Adicionais

```txt
aiofiles>=23.0.0          # Async file I/O
aiocache>=0.12.0          # Cache async com TTL
diskcache>=5.6.0          # Cache persistente em disco
```

Instale com:
```bash
uv pip install -r requirements.txt
```

---

## Uso

```bash
# Processar editais no diretório input_pdfs/
python main.py

# Uso programático
import asyncio
from main import EditalProcessor

async def processar():
    processor = EditalProcessor()
    success = await processor.process('input_pdfs/edital.pdf')
    await processor.db.close()

asyncio.run(processar())
```