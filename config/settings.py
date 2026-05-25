from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_api_key: str = Field(..., description="Clé API OpenAI")
    openai_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    ollama_base_url: str = Field(default="http://localhost:11434")
    ollama_model: str = Field(default="llama3.1")

    faiss_index_tax: str = Field(default="rag/indexes/tax_rules_index")
    faiss_index_standards: str = Field(default="rag/indexes/einvoice_standards_index")
    faiss_index_accounting: str = Field(default="rag/indexes/accounting_plan_index")

    rag_top_k: int = Field(default=5)
    rag_similarity_threshold: float = Field(default=0.7)

    extraction_confidence_threshold: float = Field(default=0.8)
    classification_confidence_threshold: float = Field(default=0.7)
    max_retries: int = Field(default=3)

    output_dir: str = Field(default="data/outputs")
    log_level: str = Field(default="INFO")


settings = Settings()
