"""
Orquestador principal del productor usando patrón Command y Facade
"""
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from loguru import logger

from .spotify_client import SpotifyClientFactory, SpotifyAPIClient
from .kafka_producer import KafkaProducerFactory, SpotifyKafkaProducer, MetricsObserver
from .config import config


class Command(ABC):
    """Interfaz Command para operaciones del productor"""
    
    @abstractmethod
    def execute(self) -> Dict[str, Any]:
        """Ejecuta el comando"""
        pass


class FetchCountryStatsCommand(Command):
    """Comando para obtener estadísticas de un país específico"""
    
    def __init__(self, spotify_client: SpotifyAPIClient, kafka_producer: SpotifyKafkaProducer, country_code: str):
        self.spotify_client = spotify_client
        self.kafka_producer = kafka_producer
        self.country_code = country_code
    
    def execute(self) -> Dict[str, Any]:
        """Ejecuta la obtención y envío de estadísticas para un país"""
        try:
            logger.info(f"Procesando país: {self.country_code}")
            
            # Obtener datos de Spotify
            country_stats = self.spotify_client.fetch_country_top_tracks(self.country_code)
            
            # Enviar a Kafka
            self.kafka_producer.send_country_stats(country_stats)
            
            return {
                "country_code": self.country_code,
                "status": "success",
                "tracks_count": country_stats.total_tracks,
                "timestamp": country_stats.timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error procesando {self.country_code}: {e}")
            return {
                "country_code": self.country_code,
                "status": "error",
                "error": str(e)
            }


class BatchProcessCommand(Command):
    """Comando para procesar múltiples países en lote"""
    
    def __init__(self, spotify_client: SpotifyAPIClient, kafka_producer: SpotifyKafkaProducer, 
                 country_codes: List[str], max_workers: int = 5):
        self.spotify_client = spotify_client
        self.kafka_producer = kafka_producer
        self.country_codes = country_codes
        self.max_workers = max_workers
    
    def execute(self) -> Dict[str, Any]:
        """Ejecuta el procesamiento en lote de países"""
        results = []
        start_time = time.time()
        
        logger.info(f"Iniciando procesamiento en lote de {len(self.country_codes)} países")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Crear comandos para cada país
            commands = [
                FetchCountryStatsCommand(self.spotify_client, self.kafka_producer, country)
                for country in self.country_codes
            ]
            
            # Ejecutar comandos en paralelo
            future_to_command = {
                executor.submit(command.execute): command 
                for command in commands
            }
            
            for future in as_completed(future_to_command):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error en ejecución paralela: {e}")
                    results.append({
                        "status": "error",
                        "error": str(e)
                    })
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        successful = len([r for r in results if r.get("status") == "success"])
        failed = len([r for r in results if r.get("status") == "error"])
        
        logger.info(f"Procesamiento completado - Exitosos: {successful}, Fallidos: {failed}, Tiempo: {processing_time:.2f}s")
        
        return {
            "total_countries": len(self.country_codes),
            "successful": successful,
            "failed": failed,
            "processing_time_seconds": processing_time,
            "results": results
        }


class SpotifyProducerOrchestrator:
    """
    Orquestador principal que actúa como Facade para el sistema completo
    """
    
    def __init__(self):
        self.spotify_client: SpotifyAPIClient = None
        self.kafka_producer: SpotifyKafkaProducer = None
        self.metrics_observer: MetricsObserver = None
        self._is_initialized = False
        
        # Países por defecto para procesar
        self.default_countries = [
            "US", "GB", "CA", "AU", "DE", "FR", "ES", "IT", 
            "BR", "MX", "AR", "CO", "CL", "PE", "JP", "KR", 
            "IN", "SE", "NO"
        ]
    
    def initialize(self) -> None:
        """Inicializa todos los componentes del sistema"""
        try:
            logger.info("Inicializando orquestador del productor de Spotify")
            
            # Crear cliente de Spotify
            self.spotify_client = SpotifyClientFactory.create_client()
            
            # Crear productor de Kafka
            self.kafka_producer = KafkaProducerFactory.create_spotify_producer()
            
            # Obtener referencia al observer de métricas
            for observer in self.kafka_producer.observers:
                if isinstance(observer, MetricsObserver):
                    self.metrics_observer = observer
                    break
            
            # Conectar a Kafka
            self.kafka_producer.connect()
            
            self._is_initialized = True
            logger.info("Orquestador inicializado exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando orquestador: {e}")
            raise
    
    def shutdown(self) -> None:
        """Cierra todas las conexiones y limpia recursos"""
        try:
            if self.kafka_producer:
                self.kafka_producer.disconnect()
            
            self._is_initialized = False
            logger.info("Orquestador cerrado exitosamente")
            
        except Exception as e:
            logger.error(f"Error cerrando orquestador: {e}")
    
    def process_single_country(self, country_code: str) -> Dict[str, Any]:
        """Procesa un solo país"""
        if not self._is_initialized:
            raise RuntimeError("Orquestador no inicializado. Llama initialize() primero.")
        
        command = FetchCountryStatsCommand(
            self.spotify_client, 
            self.kafka_producer, 
            country_code
        )
        
        return command.execute()
    
    def process_all_countries(self, country_codes: List[str] = None, max_workers: int = 5) -> Dict[str, Any]:
        """Procesa múltiples países en paralelo"""
        if not self._is_initialized:
            raise RuntimeError("Orquestador no inicializado. Llama initialize() primero.")
        
        countries = country_codes or self.default_countries
        
        command = BatchProcessCommand(
            self.spotify_client,
            self.kafka_producer,
            countries,
            max_workers
        )
        
        return command.execute()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del procesamiento"""
        if not self.metrics_observer:
            return {"error": "Métricas no disponibles"}
        
        return self.metrics_observer.get_metrics()
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica el estado de salud del sistema"""
        health_status = {
            "orchestrator_initialized": self._is_initialized,
            "spotify_client_ready": self.spotify_client is not None,
            "kafka_producer_ready": self.kafka_producer is not None and self.kafka_producer._producer is not None,
            "timestamp": time.time()
        }
        
        # Verificar conectividad básica
        try:
            if self.spotify_client:
                # Intentar obtener token (sin hacer request completo)
                self.spotify_client.auth_strategy.get_access_token()
                health_status["spotify_auth_ok"] = True
        except Exception as e:
            health_status["spotify_auth_ok"] = False
            health_status["spotify_error"] = str(e)
        
        health_status["overall_healthy"] = all([
            health_status["orchestrator_initialized"],
            health_status["spotify_client_ready"],
            health_status["kafka_producer_ready"],
            health_status.get("spotify_auth_ok", False)
        ])
        
        return health_status
