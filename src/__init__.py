"""
Pipeline de datos de Spotify usando Apache Kafka
"""

__version__ = "1.0.0"
__author__ = "Sebastian Pasar"
__description__ = "Pipeline de datos de Spotify usando Apache Kafka"

# Importaciones del productor
from .kafka_producer_spotify.config import config
from .kafka_producer_spotify.models import SpotifyTrack, SpotifyCountryStats, SpotifyMessage
from .kafka_producer_spotify.spotify_client import SpotifyClientFactory
from .kafka_producer_spotify.kafka_producer import KafkaProducerFactory
from .kafka_producer_spotify.producer_orchestrator import SpotifyProducerOrchestrator
from .kafka_producer_spotify.main import SpotifyProducerApp

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
