from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(default="learner004")
    OPENAI_BASE_URL: str = Field(default="https://keygateway.arshnivlabs.com/")
    MODEL_NAME: str = Field(default="gpt-4o-mini")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    CHROMA_PERSIST_DIR: str = Field(default="./chroma_db")
    CHROMA_COLLECTION: str = Field(default="telecom_incidents")
    BM25_INDEX_PATH: str = Field(default="./bm25_index.pkl")
    DATA_CSV_PATH: str = Field(default="../data/telecom_incidents.csv")
    LOG_LEVEL: str = Field(default="INFO")
    MAX_RETRIEVED_DOCS: int = Field(default=20)
    TOP_K_RESULTS: int = Field(default=5)
    RRF_K: int = Field(default=60)
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    SERVICENOW_INSTANCE: str = Field(default="https://dev385660.service-now.com")
    SERVICENOW_USER: str = Field(default="admin")
    SERVICENOW_PASSWORD: str = Field(default="7b0LJ+*GatxN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
