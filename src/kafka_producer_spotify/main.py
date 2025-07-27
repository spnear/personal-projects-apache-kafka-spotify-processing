"""
Aplicación principal del productor de Spotify
"""
import signal
import sys
import time
from typing import Optional
import schedule
from loguru import logger

from .producer_orchestrator import SpotifyProducerOrchestrator
from .config import config


class SpotifyProducerApp:
    """Aplicación principal del productor"""
    
    def __init__(self):
        self.orchestrator: Optional[SpotifyProducerOrchestrator] = None
        self.running = False
        self._setup_logging()
        self._setup_signal_handlers()
    
    def _setup_logging(self) -> None:
        """Configura el sistema de logging"""
        logger.remove()  # Remover handler por defecto
        
        # Configurar formato
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )
        
        # Handler para consola
        logger.add(
            sys.stdout,
            format=log_format,
            level=config.log_level,
            colorize=True
        )
        
        # Handler para archivo
        logger.add(
            "logs/spotify_producer.log",
            format=log_format,
            level="DEBUG",
            rotation="1 day",
            retention="7 days",
            compression="zip"
        )
    
    def _setup_signal_handlers(self) -> None:
        """Configura manejadores de señales para cierre graceful"""
        def signal_handler(signum, frame):
            logger.info(f"Señal {signum} recibida. Cerrando aplicación...")
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _scheduled_job(self) -> None:
        """Job que se ejecuta según el schedule configurado"""
        try:
            logger.info("Iniciando job programado de obtención de datos")
            
            result = self.orchestrator.process_all_countries()
            
            logger.info(
                f"Job completado - Países procesados: {result['total_countries']}, "
                f"Exitosos: {result['successful']}, "
                f"Fallidos: {result['failed']}, "
                f"Tiempo: {result['processing_time_seconds']:.2f}s"
            )
            
            # Mostrar métricas
            metrics = self.orchestrator.get_metrics()
            logger.info(f"Métricas acumuladas: {metrics}")
            
        except Exception as e:
            logger.error(f"Error en job programado: {e}")
    
    def initialize(self) -> None:
        """Inicializa la aplicación"""
        try:
            logger.info("Inicializando aplicación del productor de Spotify")
            
            # Crear y configurar orquestador
            self.orchestrator = SpotifyProducerOrchestrator()
            self.orchestrator.initialize()
            
            # Verificar salud del sistema
            health = self.orchestrator.health_check()
            if not health["overall_healthy"]:
                raise RuntimeError(f"Sistema no saludable: {health}")
            
            logger.info("Aplicación inicializada exitosamente")
            
        except Exception as e:
            logger.error(f"Error inicializando aplicación: {e}")
            raise
    
    def start_scheduler(self) -> None:
        """Inicia el scheduler para ejecución periódica"""
        if not self.orchestrator:
            raise RuntimeError("Aplicación no inicializada")
        
        # Configurar schedule
        schedule.every(config.fetch_interval_minutes).minutes.do(self._scheduled_job)
        
        logger.info(f"Scheduler configurado para ejecutar cada {config.fetch_interval_minutes} minutos")
        
        # Ejecutar job inicial
        logger.info("Ejecutando job inicial...")
        self._scheduled_job()
        
        # Loop principal del scheduler
        self.running = True
        logger.info("Iniciando loop del scheduler...")
        
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Error en loop del scheduler: {e}")
                time.sleep(5)  # Esperar antes de reintentar
    
    def run_once(self) -> None:
        """Ejecuta el procesamiento una sola vez"""
        if not self.orchestrator:
            raise RuntimeError("Aplicación no inicializada")
        
        logger.info("Ejecutando procesamiento único...")
        self._scheduled_job()
    
    def stop(self) -> None:
        """Detiene la aplicación de forma graceful"""
        logger.info("Deteniendo aplicación...")
        
        self.running = False
        
        if self.orchestrator:
            self.orchestrator.shutdown()
        
        logger.info("Aplicación detenida")
    
    def status(self) -> None:
        """Muestra el estado actual de la aplicación"""
        if not self.orchestrator:
            logger.info("Aplicación no inicializada")
            return
        
        health = self.orchestrator.health_check()
        metrics = self.orchestrator.get_metrics()
        
        logger.info("=== ESTADO DE LA APLICACIÓN ===")
        logger.info(f"Sistema saludable: {health['overall_healthy']}")
        logger.info(f"Orquestador inicializado: {health['orchestrator_initialized']}")
        logger.info(f"Cliente Spotify listo: {health['spotify_client_ready']}")
        logger.info(f"Productor Kafka listo: {health['kafka_producer_ready']}")
        logger.info(f"Autenticación Spotify OK: {health.get('spotify_auth_ok', 'N/A')}")
        
        logger.info("=== MÉTRICAS ===")
        logger.info(f"Mensajes enviados: {metrics.get('messages_sent', 0)}")
        logger.info(f"Mensajes fallidos: {metrics.get('messages_failed', 0)}")
        logger.info(f"Países procesados: {metrics.get('countries_processed', 0)}")
        logger.info(f"Tasa de éxito: {metrics.get('success_rate', 0):.2%}")


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Productor de estadísticas de Spotify")
    parser.add_argument(
        "--mode", 
        choices=["scheduler", "once", "status"], 
        default="scheduler",
        help="Modo de ejecución"
    )
    
    args = parser.parse_args()
    
    app = SpotifyProducerApp()
    
    try:
        app.initialize()
        
        if args.mode == "scheduler":
            app.start_scheduler()
        elif args.mode == "once":
            app.run_once()
        elif args.mode == "status":
            app.status()
            
    except KeyboardInterrupt:
        logger.info("Interrupción por teclado recibida")
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)
    finally:
        app.stop()


if __name__ == "__main__":
    main()
