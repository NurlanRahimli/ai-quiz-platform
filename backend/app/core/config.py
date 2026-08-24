from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: str = "http://localhost:5173"
    email_otp_expire_minutes: int = 10
    email_otp_resend_cooldown_seconds: int = 60
    email_otp_max_attempts: int = 5

    twilio_api_key_sid: str | None = None
    twilio_api_key_secret: str | None = None
    twilio_from_email: str = "no-reply@nurlanquiz.org"
    twilio_from_name: str = "QuizApp"

    @property
    def cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()