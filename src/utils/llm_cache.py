"""
Cache de resultados de LLM para evitar chamadas duplicadas.
Usa hash do prompt + system_prompt como chave.
"""
import hashlib
import json
from typing import Optional, Tuple
from pathlib import Path
from diskcache import Cache

class LLMCache:
    """Cache persistente em disco para resultados de LLM."""

    def __init__(self, cache_dir: str = ".cache/llm", ttl: int = 86400):
        """
        Args:
            cache_dir: Diretório para cache persistente
            ttl: Time-to-live em segundos (default: 24h)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache = Cache(str(self.cache_dir))
        self.ttl = ttl
        self.hits = 0
        self.misses = 0

    def _generate_key(self, prompt: str, system_prompt: str, model: str) -> str:
        """Gera chave única baseada nos inputs."""
        content = f"{model}|{system_prompt}|{prompt}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        system_prompt: str,
        model: str
    ) -> Optional[Tuple[str, str]]:
        """
        Recupera resultado do cache.

        Returns:
            Tuple (content, model_used) ou None se não existir
        """
        key = self._generate_key(prompt, system_prompt, model)
        result = self.cache.get(key)

        if result:
            self.hits += 1
            return result

        self.misses += 1
        return None

    def set(
        self,
        prompt: str,
        system_prompt: str,
        model: str,
        content: str,
        model_used: str
    ):
        """Salva resultado no cache."""
        key = self._generate_key(prompt, system_prompt, model)
        self.cache.set(key, (content, model_used), expire=self.ttl)

    def clear(self):
        """Limpa todo o cache."""
        self.cache.clear()

    def stats(self) -> dict:
        """Retorna estatísticas de uso do cache."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_requests": total,
            "hit_rate_percent": round(hit_rate, 2),
            "cache_size": len(self.cache)
        }