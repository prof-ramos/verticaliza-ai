import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def log_extraction_start(pdf_path, source_type):
    logger.info(f"Iniciando extração de {pdf_path} (fonte: {source_type})")

def log_extraction_complete(pages, text_length, time_taken):
    logger.info(f"Extração concluída: {pages} páginas, {text_length} caracteres, {time_taken:.2f}s")

def log_llm_call(model, prompt_length, response_length):
    logger.info(f"LLM call: {model}, prompt: {prompt_length} chars, response: {response_length} chars")