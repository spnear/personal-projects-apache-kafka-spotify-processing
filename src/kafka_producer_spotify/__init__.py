"""
Productor de estadísticas de Spotify para Apache Kafka
"""

__version__ = "1.0.0"
__author__ = "Sebastian Pasar"
__description__ = "Productor de datos de Spotify para Apache Kafka"

from .config import config
from .models import SpotifyTrack, SpotifyCountryStats, SpotifyMessage
from .spotify_client import SpotifyClientFactory
from .kafka_producer import KafkaProducerFactory
from .producer_orchestrator import SpotifyProducerOrchestrator
from .main import SpotifyProducerApp

__all__ = [
    "config",
    "SpotifyTrack",
    "SpotifyCountryStats", 
    "SpotifyMessage",
    "SpotifyClientFactory",
    "KafkaProducerFactory",
    "SpotifyProducerOrchestrator",
    "SpotifyProducerApp"
]
