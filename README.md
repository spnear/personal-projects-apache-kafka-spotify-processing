# Proyecto Apache Kafka con Docker

Este proyecto implementa un cluster sencillo de Apache Kafka utilizando Docker y Docker Compose para desarrollo local.

## Arquitectura

El cluster incluye:
- **Zookeeper**: Coordinación y gestión de metadatos
- **Kafka Broker**: Servidor principal de mensajería
- **Kafka UI**: Interfaz web para monitoreo

## Requisitos

- Docker Desktop instalado y corriendo
- Docker Compose
- Al menos 4GB de RAM disponible

## Iniciar el Cluster

Para iniciar el cluster de Kafka, ejecuta:

```bash
docker-compose up -d
```

Verificar que los servicios estén corriendo:

```bash
docker-compose ps
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

### Envío y Recepción de Mensajes

#### Productor (Enviar mensajes)

```bash
# Abrir consola de productor
docker exec -it kafka-broker kafka-console-producer \
    --topic test-topic \
    --bootstrap-server localhost:9092

# Luego escribe mensajes línea por línea
# Presiona Ctrl+C para salir
```

#### Consumidor (Recibir mensajes)

```bash
# Consumir desde el inicio
docker exec -it kafka-broker kafka-console-consumer \
    --topic test-topic \
    --bootstrap-server localhost:9092 \
    --from-beginning

# Consumir solo mensajes nuevos
docker exec -it kafka-broker kafka-console-consumer \
    --topic test-topic \
    --bootstrap-server localhost:9092
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

### Variables de Entorno Importantes

```yaml
# Kafka
KAFKA_BROKER_ID: 1
KAFKA_ZOOKEEPER_CONNECT: 'zookeeper:2181'
KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:29092,PLAINTEXT_HOST://localhost:9092
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'

# Zookeeper
ZOOKEEPER_CLIENT_PORT: 2181
ZOOKEEPER_TICK_TIME: 2000
```

## Ejemplo de Prueba Completa

1. **Iniciar el cluster**:
   ```bash
   docker-compose up -d
   ```

2. **Crear un topic**:
   ```bash
   docker exec kafka-broker kafka-topics --create \
       --topic mensajes-prueba \
       --bootstrap-server localhost:9092 \
       --partitions 3 \
       --replication-factor 1
   ```

3. **Abrir terminal para consumidor**:
   ```bash
   docker exec -it kafka-broker kafka-console-consumer \
       --topic mensajes-prueba \
       --bootstrap-server localhost:9092 \
       --from-beginning
   ```

4. **En otra terminal, abrir productor**:
   ```bash
   docker exec -it kafka-broker kafka-console-producer \
       --topic mensajes-prueba \
       --bootstrap-server localhost:9092
   ```

5. **Enviar mensajes**:
   ```
   Hola Kafka!
   Este es mi primer mensaje
   Kafka funciona correctamente
   ```

6. **Verificar en Kafka UI**: http://localhost:8080

## Troubleshooting

### Problemas Comunes

1. **Error de conexión**:
   - Verificar que Docker esté corriendo
   - Comprobar que los puertos no estén ocupados

2. **Servicios no inician**:
   ```bash
   docker-compose logs kafka
   docker-compose logs zookeeper
   ```

3. **Limpiar datos**:
   ```bash
   docker-compose down -v
   docker system prune -f
   ```

### Verificar Estado del Cluster

```bash
# Estado de los contenedores
docker-compose ps

# Logs en tiempo real
docker-compose logs -f

# Verificar conectividad
docker exec kafka-broker kafka-broker-api-versions --bootstrap-server localhost:9092
```

## Estructura del Proyecto

```
directory/
├── docker-compose.yml      # Configuración de servicios
├── Dockerfile             # Imagen personalizada de Kafka
└── README.md              # Esta documentación
```

## Notas

- Este setup está optimizado para desarrollo local
- Para producción, considera configuraciones adicionales de seguridad
- Los datos se persisten en volúmenes de Docker
- El cluster se configura automáticamente para crear topics dinámicamente
