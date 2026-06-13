"""
mysql_consumer.py — MySQL 数据库轮询消费者

周期性查询 MySQL 数据库，将统计汇总数据推入 DataEngine。

设计要点:
  - 使用 aiomysql（异步驱动），不阻塞事件循环
  - 连接失败 / 查询失败时：log 警告，返回默认值，不崩溃
  - MySQL 未配置（.env 中无 MYSQL_HOST）时：优雅跳过，不报错
  - 查询结果通过 engine.push_data("mysql", results) 推入引擎

数据流:
  MySQL ──(poll)── mysql_consumer ── engine.push_data("mysql") ── DataEngine
                                                                        │
  (引擎内部合并: MySQL 标量值 + IEC 61850 line_data  完整 Chart4Payload)

写给嵌入式开发者:
  类似 MODBUS RTU 轮询：定时读取保持寄存器的值，转换后写入共享内存。
  这里"共享内存" = DataEngine 内部缓存。
"""

import asyncio
import logging
import os
from typing import TYPE_CHECKING

import aiomysql

if TYPE_CHECKING:
    from src.engine import DataEngine

from src.config_loader import load_mysql_queries, MysqlQuery

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# 默认轮询间隔（秒）
# ══════════════════════════════════════════════════════════════════════════

DEFAULT_POLL_INTERVAL = 5  # MySQL 统计类数据变化慢，5 秒一次足够


# ══════════════════════════════════════════════════════════════════════════
# Transform 编译（与 chart4_transformer 共用逻辑）
# ══════════════════════════════════════════════════════════════════════════

def _compile_transform(expr: str):
    """将 YAML 中的 transform 字符串编译为可调用函数"""
    safe_builtins = {"abs": abs, "int": int, "round": round, "min": min, "max": max}
    try:
        return eval(f"lambda v: {expr}", {"__builtins__": safe_builtins}, {})
    except Exception:
        logger.warning(f"无法编译 transform 表达式: {expr}，使用恒等")
        return lambda v: v


# ══════════════════════════════════════════════════════════════════════════
# MySQL 连接配置
# ══════════════════════════════════════════════════════════════════════════

def _get_mysql_config() -> dict | None:
    """从 .env 读取 MySQL 连接参数。未配置时返回 None"""
    host = os.getenv("MYSQL_HOST")
    if not host:
        return None

    return {
        "host": host,
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "db": os.getenv("MYSQL_DATABASE", "sc_datav"),
    }


# ══════════════════════════════════════════════════════════════════════════
# 主轮询循环
# ══════════════════════════════════════════════════════════════════════════

async def start_mysql_polling(
    engine: "DataEngine",
    interval: int = DEFAULT_POLL_INTERVAL,
) -> None:
    """
    启动 MySQL 轮询消费者（长期运行协程）。

    参数:
        engine:   中央数据引擎实例（由 main.py 传入）
        interval: 轮询间隔（秒）

    行为:
        1. 检查 MySQL 是否已配置，未配置则跳过
        2. 加载 mapping.yaml 中的 MySQL 查询定义
        3. 建立连接池，进入无限轮询循环
        4. 每轮：执行所有查询  编译结果  engine.push_data("mysql")
        5. 查询失败时使用 default 值，不中断轮询

    退出:
        由 main.py 在 shutdown 时通过 asyncio.Task.cancel() 触发
    """
    # ── 检查 MySQL 配置 ──
    mysql_cfg = _get_mysql_config()
    if mysql_cfg is None:
        logger.info(
            "ℹ  未检测到 MYSQL_HOST 环境变量，跳过 MySQL 轮询。\n"
            "   如需启用 MySQL 数据源，请在 .env 中配置:\n"
            "   MYSQL_HOST=127.0.0.1\n"
            "   MYSQL_PORT=3306\n"
            "   MYSQL_USER=root\n"
            "   MYSQL_PASSWORD=your_password\n"
            "   MYSQL_DATABASE=sc_datav"
        )
        # 保持协程存活但不做任何事（防止 main.py 的 create_task 因立即返回而误判完成）
        try:
            while True:
                await asyncio.sleep(3600)  # 每小时醒一次检查环境是否已配置
        except asyncio.CancelledError:
            return

    # ── 加载 MySQL 查询定义 ──
    queries: list[MysqlQuery] = []
    for chart_name in ("chart4",):
        qs = load_mysql_queries(chart_name)
        queries.extend(qs)
        logger.info(f"加载 {chart_name} MySQL 查询: {len(qs)} 条")

    if not queries:
        logger.warning("没有 MySQL 查询定义，跳过轮询")
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            return

    # ── 建立连接池 ──
    try:
        pool = await aiomysql.create_pool(
            host=mysql_cfg["host"],
            port=mysql_cfg["port"],
            user=mysql_cfg["user"],
            password=mysql_cfg["password"],
            db=mysql_cfg["db"],
            autocommit=True,
            minsize=1,
            maxsize=3,
        )
        logger.info(
            f"MySQL 连接池已建立: "
            f"{mysql_cfg['user']}@{mysql_cfg['host']}:{mysql_cfg['port']}/{mysql_cfg['db']}"
        )
    except Exception as e:
        logger.error(f"MySQL 连接失败: {e}。将使用默认值运行。")
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            return

    # ── 主轮询循环 ──
    logger.info(f"MySQL 轮询已启动，间隔={interval}s，共 {len(queries)} 条查询")
    try:
        while True:
            results: dict[str, int | float] = {}

            async with pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    for q in queries:
                        try:
                            await cursor.execute(q.query)
                            row = await cursor.fetchone()
                            if row and row[0] is not None:
                                raw_value = float(row[0])
                                transform_fn = _compile_transform(q.transform)
                                results[q.field] = transform_fn(raw_value)
                                logger.debug(
                                    f"MySQL [{q.field}]: raw={raw_value}, "
                                    f"transformed={results[q.field]}"
                                )
                            else:
                                logger.warning(
                                    f"MySQL [{q.field}]: 查询无结果，"
                                    f"使用默认值 {q.default}"
                                )
                                results[q.field] = q.default
                        except Exception as e:
                            logger.error(
                                f"MySQL [{q.field}] 查询失败: {e}，"
                                f"使用默认值 {q.default}"
                            )
                            results[q.field] = q.default

            # 推送结果到引擎
            if results:
                await engine.push_data("mysql", results)
                logger.debug(f"[mysql] 推送 {len(results)} 个字段到引擎")

            await asyncio.sleep(interval)

    except asyncio.CancelledError:
        logger.info("MySQL 轮询已停止")
    finally:
        pool.close()
        await pool.wait_closed()
        logger.info("MySQL 连接池已关闭")
