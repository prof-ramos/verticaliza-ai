import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

class OpenRouterClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("OPENROUTER_API_KEY"),
            base_url="https://openrouter.ai/api/v1"
        )
        self.total_cost = 0.0
        self.primary_model = os.getenv("OPENROUTER_MODEL_PRIMARY", "anthropic/claude-3-haiku")
        fallback_str = os.getenv("OPENROUTER_MODELS_FALLBACK", "openai/gpt-4o-mini,meta-llama/llama-3.1-8b-instruct")
        self.fallback_models = [m.strip() for m in fallback_str.split(",")]

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def process_with_fallback(self, prompt: str, system_prompt: str) -> tuple[str, str]:
        """Processa prompt com fallback de modelos."""
        models = [self.primary_model] + self.fallback_models
        
        for model in models:
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000
                )
                content = response.choices[0].message.content
                # Simular custo (implementar cálculo real baseado no modelo)
                self.total_cost += 0.01  # Placeholder
                return content, model
            except Exception as e:
                print(f"Erro com modelo {model}: {e}")
                continue
        
        raise Exception("Todos os modelos falharam")