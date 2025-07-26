# Dockerfile para Apache Kafka
FROM confluentinc/cp-kafka:7.4.0

# Configurar variables de entorno por defecto
ENV KAFKA_BROKER_ID=1
ENV KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
ENV KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092
ENV KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1
ENV KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1
ENV KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1
ENV KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS=0

# Exponer puerto de Kafka
EXPOSE 9092

# Comando por defecto
CMD ["kafka-server-start", "/etc/kafka/server.properties"]
