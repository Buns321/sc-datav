# sc-datav：MySQL 接入与架构升级重构实施计划

## 背景与目标
本计划用于指导 `sc-datav` 项目完成 **MySQL 接入** 与 **架构升级**。
核心目标是：**化解当前 `tcp_server.py` 权力过大的单体瓶颈，构建“多数据源采集 -> 中央引擎处理 -> 统一推送”的工业级网关架构。**

---

## Phase 1：映射层改造（配置先行）
**目标**：让系统明确“谁从 TCP 取、谁从 MySQL 取”。

1. **修改 `mapping.yaml`**
   - 为每个指标补充 `source` 字段。
   - 为不同数据源补充对应参数（如 `ref` 或 `query`）。

   ```yaml
   chart4:
     enterpriseCount:
       source: "iec61850"
       ref: "LD0/MMXU1.TotW.mag.f"
     totalRevenue:
       source: "mysql"
       query: "SELECT total FROM revenue_table ORDER BY id DESC LIMIT 1"
   ```

2. **升级 `config_loader.py`**
   - 调整配置解析逻辑。
   - 将映射配置拆分为两类指引：
     - TCP 采集器使用的配置。
     - MySQL 采集器使用的配置。

---

## Phase 2：核心解耦与 `tcp_server.py` 瘦身（重构核心）
**目标**：建立中央数据引擎，剥离 TCP Server 的广播职责。

1. **创建 `src/engine.py`（中央数据引擎）**
   - 在引擎内部实例化 `Chart4Transformer` 等 Transformer。
   - 提供统一入口：`async def push_data(self, source, data)`。
   - 在引擎内部完成多源数据合并（Buffer）。
   - 当组装出完整 `Chart4Payload` 后，由引擎统一调用 `ws_manager.broadcast()` 推送。

2. **重构并重命名 `tcp_server.py` -> `src/consumers/tcp_consumer.py`**
   - 删除对 `Chart4Transformer` 和 `ws_manager` 的直接依赖。
   - 保留 TCP 监听、粘包处理、JSON 校验。
   - 收到 `iec61850_raw` 后仅执行：`await engine.push_data("iec61850", data_points)`。

---

## Phase 3：新增 MySQL 消费者
**目标**：让系统具备主动轮询数据库的能力。

1. **引入异步驱动**
   - 在依赖中安装 `aiomysql`（或 SQLAlchemy 异步方案）。
   - 禁止使用同步 `pymysql`，避免阻塞事件循环并影响 WebSocket。

2. **创建 `src/consumers/mysql_consumer.py`**
   - 编写 `async def start_mysql_polling(engine, interval=5)`。
   - 协程内部使用 `while True` 轮询。
   - 每轮根据 YAML 中 SQL 语句查询 MySQL。
   - 将查询结果交给中央引擎：`await engine.push_data("mysql", mysql_results)`。
   - 使用 `await asyncio.sleep(interval)` 控制轮询间隔。

---

## Phase 4：启动调度与前端初始加载优化
**目标**：在 FastAPI 生命周期中串联并启动全部组件。

1. **组装 `main.py`**
   - 在 FastAPI `lifespan` 中创建全局唯一 `DataEngine`。
   - 使用 `asyncio.create_task()` 并发启动 `tcp_consumer` 和 `mysql_consumer`。

   ```python
   engine = DataEngine()
   asyncio.create_task(start_tcp_server(engine))
   asyncio.create_task(start_mysql_polling(engine))
   ```

2. **新增 HTTP GET 接口（可选但强烈推荐）**
   - 在 `main.py` 增加 `@app.get("/api/charts/4")`。
   - 用于页面刷新时主动拉取引擎中的最新缓存，避免首屏无数据。

3. **前端配合（若实施第 2 步）**
   - 在 Zustand `dataStore.ts` 增加 `fetchInitialData()`。
   - ECharts 等核心组件保持 0 代码改动。

---

## 结果预期
完成本计划后，仓库将由“单脚本集中处理”升级为可扩展的插件化架构。
后续新增 Redis、MQTT、PLC 等数据源时，只需在 `consumers/` 扩展新消费者，核心链路基本无需改动，具备更高可维护性与工程成熟度。
