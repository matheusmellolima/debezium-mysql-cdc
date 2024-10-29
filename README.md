# Change Data Capture (CDC) using Debezium for MySQL

## How to execute this project?

Run `docker compose up -d` to create all services you need. This project uses Docker images from [Debezium tutorial examples](https://github.com/debezium/debezium-examples/tree/main/tutorial).

After all containers are running, execute the following HTTP POST request:
```
POST /connectors HTTP/1.1
Host: connect.example.com
Content-Type: application/json
Accept: application/json

{
  "name": "inventory-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "mysql",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "dbz",
    "database.server.id": "184054",
    "topic.prefix": "dbserver1",
    "database.include.list": "inventory",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
    "schema.history.internal.kafka.topic": "schema-changes.inventory"
  }
}
```

You can copy this CURL command if you want to:
```
curl -i -X POST -H "Accept:application/json" -H  "Content-Type:application/json" http://localhost:8083/connectors/ -d '
{
  "name": "inventory-connector",
  "config": {
    "connector.class": "io.debezium.connector.mysql.MySqlConnector",
    "tasks.max": "1",
    "database.hostname": "mysql",
    "database.port": "3306",
    "database.user": "debezium",
    "database.password": "dbz",
    "database.server.id": "184054",
    "topic.prefix": "dbserver1",
    "database.include.list": "inventory",
    "schema.history.internal.kafka.bootstrap.servers": "kafka:9092",
    "schema.history.internal.kafka.topic": "schema-changes.inventory"
  }
}'
```

This will create the Debezium MySQL Connector and configure the topics Debezium will send updates to. With this particular configuration all tables in the database list `database.include.list` is set to be included. But you can set specifically what you want to include by using:
* `"table.include.list": "inventory.user, inventory.customers"`
* `table.exclude.list`
* `column.include.list`
* `column.exclude.list`

you can't use one `include` config with a `exclude` config, and vice versa.

Now that Debezium is set, run the Python Script `python producer.py` to execute inserts in the Database. This script will create 100 new records in the `user` table. You don't need to worry about creating the table, the script will do it. 

Then go to the page `http://localhost:8080`, that's a UI for Kafka in which you can check the topics and their messages. There should be 7 topics with the prefix `dbserver1.inventory`, one for each table in the database. There should be new messages every time something changes in the database.

You can also consume Kafka from your console by executing the command:
```
docker compose exec kafka /kafka/bin/kafka-console-consumer.sh --bootstrap-server kafka:9092 --from-beginning --property print.key=true --topic dbserver1.inventory.user
```

## Few helpful commands to debug this project

### Creating a Debezium Connector

Debezium is configured by using the [Kafka Connect REST API Interface for Confluent Platform
](https://docs.confluent.io/platform/current/connect/references/restapi.html). So you need to send HTTP requests for everything.

Creating connector for MySQL database by replacing the @register-mysql-connector.json with the JSON content in between quotes '{}':

```
curl -i -X POST -H "Accept:application/json" -H  "Content-Type:application/json" http://localhost:8083/connectors/ -d @register-mysql-connector.json
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

### Updating a Debezium Connector config

```
curl -i -X PUT -H "Accept:application/json" -H "Content-Type:application/json" localhost:8083/connectors/debezium-mysql-cdc-connector/config -d @register-mysql-connector.json
```

### Deleting Debeziumn Connectors

```
curl -i -X DELETE localhost:8083/connectors/debezium-mysql-cdc-connector/
```

### Restarting a connector

```
curl -i -X POST http://localhost:8083/connectors/debezium-mysql-cdc-connector/restart
```

### Checking connectors' health

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

### Enabling Binary Logs for MySQL

First, connect to the database using the following command (this command will ask for the database ROOT password, which you can take a look at the Docker Compose):

```
docker compose exec -it mysql mysql -uroot -p
```

By using this interface, you can run SQL commands into your MySQL database.

There are a few ways to check if binary logs are available depending on your version of MySQL database:

1: 
```
SELECT variable_value as "BINARY LOGGING STATUS (log-bin) ::"
FROM information_schema.global_variables WHERE variable_name='log_bin';
```

2:
```
SELECT variable_value as "BINARY LOGGING STATUS (log-bin) ::"
FROM performance_schema.global_variables WHERE variable_name='log_bin';
```

3: 
```
show binary logs;
```

If binary logs are not ON, run the following commands:
```
docker compose exec -it mysql /bin/bash
yum install vim
vim etc/my.cnf
```

Remove the line `# log_bin` and add the following lines in the same place:
```
server-id         = 223344
log_bin           = mysql-bin
binlog_format     = ROW
binlog_row_image  = FULL
```

Now, let's go into details:

``server-id`` -> it's unique for each server and replication client in the MySQL cluster.

``log_bin`` -> it's the base name of the sequence of binlog files.

``binlog_format`` -> must be set to ROW or row.

``binlog_row_image`` -> must be set to FULL or full.

After setting up Binary Logs, restart the MySQL server with the command.

```
docker compose restart mysql
```

### Kafka commands

Debezium creates all topics needed and it's a self-service platform that can handle its self configuration, but if you want to configure Kafka yourself, you can use the UI under `http://localhost:8080`.
