from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Configuration for Pydantic Settings to load environment variables
    # from a .env file, crucial for local development and deployment.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Create a settings instance to be imported throughout the application.
# This ensures that configuration values are loaded once and consistently used.
settings = Settings()