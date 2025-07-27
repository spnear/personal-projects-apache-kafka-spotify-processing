"""
Configuración del proyecto usando el patrón Singleton
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic"""
    
    # Spotify API
    spotify_client_id: str = Field(..., env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(..., env="SPOTIFY_CLIENT_SECRET")
    
    # Kafka
    kafka_bootstrap_servers: str = Field(default="localhost:9092", env="KAFKA_BOOTSTRAP_SERVERS")
    kafka_topic: str = Field(default="spotify-stats", env="KAFKA_TOPIC")
    
    # Producer
    fetch_interval_minutes: int = Field(default=60, env="FETCH_INTERVAL_MINUTES")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class ConfigSingleton:
    """Singleton para la configuración"""
    _instance: Optional['ConfigSingleton'] = None
    _settings: Optional[Settings] = None
    
    def __new__(cls) -> 'ConfigSingleton':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def settings(self) -> Settings:
        if self._settings is None:
            self._settings = Settings()
        return self._settings


# Instancia global de configuración
config = ConfigSingleton().settings
