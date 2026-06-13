"""
consumers/ — 数据消费者集合

每个消费者负责一种数据源的接入。
消费者之间互不依赖，都通过 DataEngine.push_data() 汇聚数据。

当前消费者：
  - tcp_consumer:   接收 IEC 61850 网关的原始 TCP 报文（Line-delimited JSON）
  - mysql_consumer: 轮询 MySQL 数据库统计表（aiomysql 异步驱动）

后续扩展：
  - mqtt_consumer:  订阅 MQTT Broker 的消息
  - redis_consumer: 订阅 Redis Pub/Sub 频道
  - plc_consumer:   通过 Modbus TCP 读取 PLC 寄存器
"""
