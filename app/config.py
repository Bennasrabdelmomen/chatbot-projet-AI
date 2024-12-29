import logging

# Configuration constants
OLLAMA_SERVER = "http://localhost:11434"
MODEL_NAME = "qwen2.5:7b-instruct"

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
