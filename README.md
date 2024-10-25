# Change Data Capture (CDC) using Debezium for MySQL

## Kafka commands

### Create Kafka Topics

First, connect to container's bash.

```
docker exec -it debezium-mysql-cdc-kafka bash
```

Instead of `localhost`, use the IP you can find by inspecting the container `docker inspect debezium-mysql-cdc-kafka`.


```
bin/kafka-topics.sh --create --topic schema-changes.debezium_demo --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

### Produce and consume messages

Producing

```
bin/kafka-console-producer.sh --broker-list localhost:9092 --topic test-topic
```

Consuming

```
bin/kafka-console-consumer.sh --bootstrap-server localhost:9092 --topic test-topic --from-beginning
```

## MySQL commands

First, connect to the database through command line

```
docker exec -it debezium-mysql-cdc-mysql mysql -uroot -p
```

### Create database

```
create database debezium_demo;
```

```
use debezium_demo;
```

### Create table

```
create table user (
    user_id varchar(50) primary key,
    first_name varchar(50),
    last_name varchar(50),
    city varchar(50),
    state varchar(50),
    zipcode varchar(10)
);
```

Describe table "user"

```
desc user;
```

### Insert rows

Insert a row into "user" table

```
insert into user values (1, "John", "Doe", "Seattle", "Washington", "98101");
```

### Select table

Show rows from table

```
select * from user;
```

## Debezium

* [Kafka Connect REST Interface for Confluent Platform
](https://docs.confluent.io/platform/current/connect/references/restapi.html)

### Create connector

Creating connector for debezium-demo database:

```
curl -i -X POST -H "Accept:application/json" -H "Content-Type:application/json" http://localhost:8083/connectors/ -d '
{
  "name": "debezium-mysql-cdc-connector",  
  "config": {  
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "database.hostname": "debezium-mysql-cdc-mysql",  
    "database.port": "3306",
    "database.user": "root",
    "database.password": "password",
    "database.dbname": "debezium",
    "database.server.id": "10101",
    "database.server.name": "debezium",
    "topic.prefix": "dbz",
    "table.include.list": "user",
    "database.history.kafka.bootstrap.servers": "debezium-mysql-cdc-kafka:29092",  
    "database.history.kafka.topic": "debezium-mysql-cdc-connector-kafka-history"
  }
}'
```

``"name"`` -> Name of the connector. It should be unique in the Kafka Connect cluster.

``"config.connector.class"`` -> Connector class.

``"task.max"`` -> In this case, only 1 class should operate at max. This ensures proper order while reading database log.

``"database.server.id"`` and ``"database.server.name"`` -> Work as identifyier for the MySQL server and they are supposed to be unique values. The name will be used as prefix for the Kafka topics.

``"database.include.list"`` -> A list of databases separated by commas that should be extracted to Debezium. Same for `"table.include.list"`

``"database.history.kafka.bootstrap.servers"`` -> Kafka Servers to push the database history.

``"database.history.kafka.topic"`` -> The place where the connector will push data while reading the database log.

``"debezium.source.database.history"`` -> You need to specify debezium.source.database.history property for the mysql connector. Its default value is ``io.debezium.relational.history.KafkaDatabaseHistory``, so for non-Kafka deployments please set one of the following values:

* `io.debezium.relational.history.FileDatabaseHistory` (along with debezium.source.database.history.file.filename property);
* ``io.debezium.relational.history.MemoryDatabaseHistory`` for test environments.

### Update connector config

```
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/debezium-mysql-cdc-connector/config -d '
{
  "connector.class": "io.debezium.connector.mysql.MySqlConnector",
  "tasks.max": "1",  
  "database.hostname": "debezium-mysql-cdc-mysql",  
  "database.port": "3306",
  "database.user": "root",
  "database.password": "password",
  "database.server.id": "10101",  
  "database.server.name": "debezium-demo",
  "topic.prefix": "dbz",
  "database.include.list": "debezium",  
  "database.history.kafka.bootstrap.servers": "debezium-mysql-cdc-kafka:9092",  
  "database.history.kafka.topic": "test-topic",
  "debezium.source.database.history": "io.debezium.relational.history.MemoryDatabaseHistory"
}'
```

### Delete connectors

```
curl -i -X DELETE localhost:8083/connectors/debezium-mysql-cdc-connector/
```

### Restart connector

```
curl -i -X POST http://localhost:8083/connectors/debezium-mysql-cdc-connector/restart
```

### Checking the connectors

```
curl -XGET http://localhost:8083/connectors
```

To get additional state information for each of the connectors and its tasks

```
curl -XGET http://localhost:8083/connectors?expand=status
```

To get metadata of each of the connectors such as the configuration, task information and type of connector

```
curl -XGET http://localhost:8083/connectors?expand=info
```

