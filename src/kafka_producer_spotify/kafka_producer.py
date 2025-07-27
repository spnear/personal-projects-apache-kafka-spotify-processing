"""
Productor de Kafka usando patrón Observer y Template Method
"""
import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from kafka import KafkaProducer
from kafka.errors import KafkaError
from loguru import logger

from .models import SpotifyMessage, SpotifyCountryStats
from .config import config


class MessageObserver(ABC):
    """Observer abstracto para eventos del productor"""
    
    @abstractmethod
    def on_message_sent(self, message: SpotifyMessage, metadata: Dict[str, Any]) -> None:
        """Se ejecuta cuando un mensaje es enviado exitosamente"""
        pass
    
    @abstractmethod
    def on_message_failed(self, message: SpotifyMessage, error: Exception) -> None:
        """Se ejecuta cuando falla el envío de un mensaje"""
        pass


class LoggingObserver(MessageObserver):
    """Observer que registra eventos en logs"""
    
    def on_message_sent(self, message: SpotifyMessage, metadata: Dict[str, Any]) -> None:
        logger.info(
            f"Mensaje enviado exitosamente - País: {message.country_stats.country_code}, "
            f"Tracks: {message.country_stats.total_tracks}, "
            f"Partition: {metadata.get('partition')}, "
            f"Offset: {metadata.get('offset')}"
        )
    
    def on_message_failed(self, message: SpotifyMessage, error: Exception) -> None:
        logger.error(
            f"Error enviando mensaje - País: {message.country_stats.country_code}, "
            f"Error: {str(error)}"
        )


class MetricsObserver(MessageObserver):
    """Observer que recolecta métricas"""
    
    def __init__(self):
        self.messages_sent = 0
        self.messages_failed = 0
        self.countries_processed = set()
    
    def on_message_sent(self, message: SpotifyMessage, metadata: Dict[str, Any]) -> None:
        self.messages_sent += 1
        self.countries_processed.add(message.country_stats.country_code)
    
    def on_message_failed(self, message: SpotifyMessage, error: Exception) -> None:
        self.messages_failed += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "countries_processed": len(self.countries_processed),
            "success_rate": self.messages_sent / (self.messages_sent + self.messages_failed) if (self.messages_sent + self.messages_failed) > 0 else 0
        }


class BaseKafkaProducer(ABC):
    """Clase base abstracta para productores de Kafka usando Template Method"""
    
    def __init__(self, bootstrap_servers: str, topic: str):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.observers: List[MessageObserver] = []
        self._producer: Optional[KafkaProducer] = None
    
    def add_observer(self, observer: MessageObserver) -> None:
        """Agrega un observer"""
        self.observers.append(observer)
    
    def remove_observer(self, observer: MessageObserver) -> None:
        """Remueve un observer"""
        if observer in self.observers:
            self.observers.remove(observer)
    
    def _notify_message_sent(self, message: SpotifyMessage, metadata: Dict[str, Any]) -> None:
        """Notifica a todos los observers que un mensaje fue enviado"""
        for observer in self.observers:
            try:
                observer.on_message_sent(message, metadata)
            except Exception as e:
                logger.error(f"Error en observer: {e}")
    
    def _notify_message_failed(self, message: SpotifyMessage, error: Exception) -> None:
        """Notifica a todos los observers que falló el envío"""
        for observer in self.observers:
            try:
                observer.on_message_failed(message, error)
            except Exception as e:
                logger.error(f"Error en observer: {e}")
    
    @abstractmethod
    def _create_producer(self) -> KafkaProducer:
        """Crea la instancia del productor de Kafka"""
        pass
    
    @abstractmethod
    def _prepare_message(self, country_stats: SpotifyCountryStats) -> SpotifyMessage:
        """Prepara el mensaje antes de enviarlo"""
        pass
    
    def _serialize_message(self, message: SpotifyMessage) -> bytes:
        """Serializa el mensaje a JSON bytes"""
        return json.dumps(message.dict(), ensure_ascii=False, default=str).encode('utf-8')
    
    def connect(self) -> None:
        """Conecta al cluster de Kafka"""
        try:
            self._producer = self._create_producer()
            logger.info(f"Conectado a Kafka: {self.bootstrap_servers}")
        except Exception as e:
            logger.error(f"Error conectando a Kafka: {e}")
            raise
    
    def disconnect(self) -> None:
        """Desconecta del cluster de Kafka"""
        if self._producer:
            self._producer.close()
            self._producer = None
            logger.info("Desconectado de Kafka")
    
    def send_country_stats(self, country_stats: SpotifyCountryStats) -> None:
        """Template method para enviar estadísticas de un país"""
        if not self._producer:
            raise RuntimeError("Productor no conectado. Llama connect() primero.")
        
        try:
            # Preparar mensaje
            message = self._prepare_message(country_stats)
            
            # Serializar
            serialized_message = self._serialize_message(message)
            
            # Enviar
            future = self._producer.send(
                self.topic,
                value=serialized_message,
                key=country_stats.country_code.encode('utf-8')
            )
            
            # Callback para manejar resultado
            def on_success(metadata):
                self._notify_message_sent(message, {
                    'partition': metadata.partition,
                    'offset': metadata.offset,
                    'timestamp': metadata.timestamp
                })
            
            def on_error(error):
                self._notify_message_failed(message, error)
            
            future.add_callback(on_success)
            future.add_errback(on_error)
            
        except Exception as e:
            logger.error(f"Error enviando mensaje: {e}")
            raise


class SpotifyKafkaProducer(BaseKafkaProducer):
    """Implementación concreta del productor para datos de Spotify"""
    
    def _create_producer(self) -> KafkaProducer:
        """Crea el productor de Kafka con configuración específica"""
        return KafkaProducer(
            bootstrap_servers=self.bootstrap_servers.split(','),
            value_serializer=lambda x: x,  # Ya serializamos manualmente
            key_serializer=lambda x: x,    # Ya serializamos manualmente
            acks='all',  # Esperar confirmación de todas las réplicas
            retries=3,
            retry_backoff_ms=1000,
            request_timeout_ms=30000,
            compression_type='gzip'
        )
    
    def _prepare_message(self, country_stats: SpotifyCountryStats) -> SpotifyMessage:
        """Prepara el mensaje con información adicional del productor"""
        return SpotifyMessage(
            message_id=str(uuid.uuid4()),
            country_stats=country_stats,
            producer_info={
                "producer_type": "spotify_stats_producer",
                "version": "1.0.0",
                "kafka_topic": self.topic,
                "bootstrap_servers": self.bootstrap_servers
            }
        )


class KafkaProducerFactory:
    """Factory para crear productores de Kafka"""
    
    @staticmethod
    def create_spotify_producer() -> SpotifyKafkaProducer:
        """Crea un productor para datos de Spotify con configuración por defecto"""
        producer = SpotifyKafkaProducer(
            bootstrap_servers=config.kafka_bootstrap_servers,
            topic=config.kafka_topic
        )
        
        # Agregar observers por defecto
        producer.add_observer(LoggingObserver())
        producer.add_observer(MetricsObserver())
        
        return producer
