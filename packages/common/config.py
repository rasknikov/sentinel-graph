from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./sentinel_graph.db"
    environment: str = "development"
    jwt_algorithm: str = "HS256"
    jwt_secret: str = "sentinel-graph-dev-secret"
    jwt_issuer: str = "https://identity.example.com"
    jwt_audience: str = "sentinelgraph-ai"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )


settings = Settings()
