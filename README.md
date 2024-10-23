# Change Data Capture (CDC) using Debezium for MySQL

## Create Kafka Topics

First, connect to container's bash.

```
docker exec -it debezium-mysql-cdc-kafka bash
```

Instead of `localhost`, use the IP you can find by inspecting the container `docker inspect debezium-mysql-cdc-kafka`.


```
bin/kafka-topics.sh --create --topic test-topic --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

## Produce messages to Kafka through Console

```
bin/kafka-console-producer.sh --broker-list localhost:9092 --topic test-topic
```

## Consume messages from Kafka throguh Console

```
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test-topic --from-beginning
```