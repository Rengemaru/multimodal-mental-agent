from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str = "dummy_key"
    aivis_url: str = "http://host.docker.internal:10101"
    aivis_speaker_id: int = 1
    max_turns: int = 10
    debug_mode: bool = False
    weight_mode: str = "fixed"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
