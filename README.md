# Proyecto Apache Kafka con Docker

Este proyecto implementa un cluster sencillo de Apache Kafka utilizando Docker y Docker Compose para desarrollo local, junto con un productor de Python que consulta la API de Spotify.

## Arquitectura

El cluster incluye:
- **Zookeeper**: Coordinación y gestión de metadatos
- **Kafka Broker**: Servidor principal de mensajería
- **Kafka UI**: Interfaz web para monitoreo
- **Productor de Spotify**: Aplicación Python que obtiene estadísticas de Spotify y las envía a Kafka

## Requisitos

- Docker Desktop instalado y corriendo
- Docker Compose
- Python 3.8+
- Al menos 4GB de RAM disponible
- Credenciales de Spotify API (Client ID y Client Secret)

## Configuración Inicial

### 1. Configurar Variables de Entorno

Copia el archivo de ejemplo y configura tus credenciales:

```bash
cp .env.example .env
```

Edita el archivo `.env` con tus credenciales de Spotify:

```bash
SPOTIFY_CLIENT_ID=tu_client_id_aqui
SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=spotify-stats
FETCH_INTERVAL_MINUTES=60
LOG_LEVEL=INFO
```

### 2. Configurar Entorno Virtual de Python

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Iniciar el Sistema

### 1. Iniciar el Cluster de Kafka

```bash
docker-compose up -d
```

Verificar que los servicios estén corriendo:

```bash
docker-compose ps
```

### 2. Ejecutar el Productor de Spotify

```bash
# Modo scheduler (ejecución continua)
python run_producer.py --mode scheduler

# Ejecución única
python run_producer.py --mode once

# Ver estado del sistema
python run_producer.py --mode status
```

## Comandos de Gestión

### Gestión del Cluster

```bash
# Iniciar servicios
docker-compose up -d

# Detener servicios
docker-compose down

# Ver logs
docker-compose logs -f kafka

# Reiniciar servicios
docker-compose restart
```

### Gestión de Topics

```bash
# Crear un topic
docker exec kafka-broker kafka-topics --create \
    --topic mi-topic \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1

# Listar topics
docker exec kafka-broker kafka-topics --list \
    --bootstrap-server localhost:9092

# Describir un topic
docker exec kafka-broker kafka-topics --describe \
    --topic mi-topic \
    --bootstrap-server localhost:9092

# Eliminar un topic
docker exec kafka-broker kafka-topics --delete \
    --topic mi-topic \
    --bootstrap-server localhost:9092
```

### Monitoreo de Mensajes

#### Consumir mensajes del topic de Spotify

```bash
# Consumir desde el inicio
docker exec -it kafka-broker kafka-console-consumer \
    --topic spotify-stats \
    --bootstrap-server localhost:9092 \
    --from-beginning

# Consumir solo mensajes nuevos
docker exec -it kafka-broker kafka-console-consumer \
    --topic spotify-stats \
    --bootstrap-server localhost:9092
```

## Arquitectura del Productor

El productor de Spotify implementa varios patrones de diseño:

### Patrones Implementados

- **Singleton**: Configuración global
- **Strategy**: Diferentes estrategias de autenticación con Spotify
- **Factory**: Creación de clientes y productores
- **Observer**: Notificaciones de eventos (logs, métricas)
- **Command**: Encapsulación de operaciones
- **Template Method**: Flujo de procesamiento de mensajes
- **Facade**: Orquestador que simplifica la interfaz

### Estructura del Código

```
src/
├── __init__.py                      # Inicialización del paquete principal
├── kafka_producer_spotify/         # Productor de Spotify
│   ├── __init__.py                 # Inicialización del productor
│   ├── config.py                   # Configuración usando Singleton
│   ├── models.py                   # Modelos de datos con Pydantic
│   ├── spotify_client.py           # Cliente de Spotify API con Strategy
│   ├── kafka_producer.py           # Productor de Kafka con Observer
│   ├── producer_orchestrator.py    # Orquestador principal con Command
│   └── main.py                     # Aplicación principal
└── kafka_consumer_spotify/         # Consumidor de Spotify (futuro)
    └── __init__.py                 # Inicialización del consumidor
```

## Interfaces Web

- **Kafka UI**: http://localhost:8080
  - Visualización de topics, particiones y mensajes
  - Monitoreo de consumidores y productores
  - Gestión visual del cluster

## Configuración

### Puertos Expuestos

- `2181`: Zookeeper
- `9092`: Kafka Broker
- `8080`: Kafka UI
- `9101`: JMX (métricas)

### Variables de Entorno del Productor

```bash
# Spotify API
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=spotify-stats

# Configuración del Productor
FETCH_INTERVAL_MINUTES=60
LOG_LEVEL=INFO
```

## Ejemplo de Uso Completo

1. **Iniciar el cluster**:
   ```bash
   docker-compose up -d
   ```

2. **Configurar variables de entorno**:
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales
   ```

3. **Activar entorno virtual e instalar dependencias**:
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Ejecutar el productor**:
   ```bash
   python run_producer.py --mode once
   ```

5. **Monitorear mensajes**:
   ```bash
   docker exec -it kafka-broker kafka-console-consumer \
       --topic spotify-stats \
       --bootstrap-server localhost:9092 \
       --from-beginning
   ```

6. **Ver en Kafka UI**: http://localhost:8080

## Troubleshooting

### Problemas Comunes

1. **Error de autenticación con Spotify**:
   - Verificar que las credenciales en `.env` sean correctas
   - Asegurar que la aplicación esté registrada en Spotify Developer Dashboard

2. **Error de conexión a Kafka**:
   - Verificar que Docker esté corriendo
   - Comprobar que los puertos no estén ocupados
   - Verificar logs: `docker-compose logs kafka`

3. **Problemas con el entorno virtual**:
   ```bash
   # Recrear entorno virtual
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Verificar Estado del Sistema

```bash
# Estado de los contenedores
docker-compose ps

# Logs del productor
tail -f logs/spotify_producer.log

# Estado del productor
python run_producer.py --mode status

# Verificar conectividad
docker exec kafka-broker kafka-broker-api-versions --bootstrap-server localhost:9092
```

## Estructura del Proyecto

```
personal-projects-apache-kafka-spotify-processing/
├── docker-compose.yml              # Configuración de servicios
├── Dockerfile                     # Imagen personalizada de Kafka
├── requirements.txt               # Dependencias de Python
├── .env.example                  # Ejemplo de variables de entorno
├── run_producer.py               # Script de ejecución del productor
├── src/                          # Código fuente
│   ├── __init__.py              # Inicialización del paquete principal
│   ├── kafka_producer_spotify/   # Productor de Spotify
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models.py
│   │   ├── spotify_client.py
│   │   ├── kafka_producer.py
│   │   ├── producer_orchestrator.py
│   │   └── main.py
│   └── kafka_consumer_spotify/   # Consumidor de Spotify (futuro)
│       └── __init__.py
├── logs/                         # Logs de la aplicación
└── README.md                     # Esta documentación
```

## Notas

- Este setup está optimizado para desarrollo local
- Para producción, considera configuraciones adicionales de seguridad
- Los datos se persisten en volúmenes de Docker
- El cluster se configura automáticamente para crear topics dinámicamente
- El productor procesa 19 países por defecto cada hora
- Los logs se rotan diariamente y se mantienen por 7 días
