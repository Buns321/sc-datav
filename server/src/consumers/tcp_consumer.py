"""
tcp_consumer.py — TCP 数据消费者

从原始 tcp_server.py 重构而来。
职责被精简为：接收 TCP 报文  解析 JSON  推入 DataEngine。

与旧 tcp_server.py 的核心区别：
  - 不再直接依赖 Chart4Transformer（由引擎内部管理）
  - 不再直接依赖 ws_manager（由引擎统一广播）
  - 仅保留 TCP 层逻辑：监听、粘包拆包、JSON 校验、消息类型路由

写给嵌入式开发者：
  这个模块 = 串口接收中断服务函数 + Modbus 帧解析 + 数据路由
  它只负责"收"和"转发"，不负责"怎么用"。
"""

import asyncio
import json
import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.engine import DataEngine

logger = logging.getLogger(__name__)


async def handle_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter,
    engine: "DataEngine",
):
    """
    处理单个 TCP 客户端连接。

    每个连接有独立的 reader/writer，但共享同一个 engine 实例。
    引擎内部通过 asyncio.Lock 保证并发安全。

    参数:
        reader:  用于读取客户端数据的流
        writer:  用于向客户端回复数据的流（本消费者通常不回复）
        engine:  中央数据引擎实例（由 main.py 在启动时传入）
    """
    client_addr = writer.get_extra_info("peername")
    logger.info(f"TCP 新连接接入: {client_addr}")

    try:
        while True:
            # ── 逐行读取（Line-delimited JSON 协议） ──
            line_bytes = await reader.readline()

            if not line_bytes:
                logger.info(f"TCP 客户端断开: {client_addr}")
                break

            # ── 解码与清理 ──
            line_str = line_bytes.decode("utf-8").strip()
            if not line_str:
                continue

            logger.debug(f"收到原始报文 ({client_addr}): {line_str}")

            # ── JSON 解析（非阻塞校验） ──
            try:
                message = json.loads(line_str)
            except json.JSONDecodeError as e:
                logger.error(f"报文不是合法的 JSON ({client_addr}): {e}")
                continue

            # ── 提取通用字段 ──
            msg_type = message.get("type", "")
            timestamp = message.get("timestamp", "")

            # ── 分支路由：根据消息类型选择不同的引擎入口 ──

            if msg_type == "iec61850_raw":
                # 网关发出的结构化数据对象列表
                data_points = message.get("data_points")
                if not data_points:
                    logger.warning(f"iec61850_raw 缺少 data_points 字段 ({client_addr})")
                    continue

                device = message.get("device", "unknown")
                logger.info(
                    f" [{msg_type}] {len(data_points)} 数据对象, "
                    f"设备={device} ({client_addr}), ts={timestamp}"
                )
                await engine.push_data("iec61850", data_points)

            else:
                logger.warning(f"未知消息类型 ({client_addr}): {msg_type}")
                continue

    except ConnectionResetError:
        logger.info(f"TCP 连接被重置: {client_addr}")
    except Exception as e:
        logger.error(f"TCP 处理出错 ({client_addr}): {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
        logger.info(f"TCP 连接已关闭: {client_addr}")


async def start_tcp_consumer(
    engine: "DataEngine",
    host: str = "127.0.0.1",
    port: int = 9000,
) -> asyncio.Server:
    """
    启动 TCP 消费者服务。

    参数:
        engine: 中央数据引擎实例
        host:   监听地址（"0.0.0.0" 接受所有来源，"127.0.0.1" 仅本机）
        port:   监听端口

    返回:
        asyncio.Server 对象，可用于停止服务

    使用方式:
        server = await start_tcp_consumer(engine)
        # ... 应用运行中 ...
        server.close()
        await server.wait_closed()
    """
    #  使用 lambda 将 engine 绑定到每个连接的 handler
    async def handler(reader, writer):
        await handle_client(reader, writer, engine)

    server = await asyncio.start_server(handler, host, port)

    addr = server.sockets[0].getsockname() if server.sockets else (host, port)
    logger.info(f"TCP Consumer 已启动: tcp://{addr[0]}:{addr[1]}")
    logger.info(f"等待上位机连接...")

    return server


async def start_tcp_from_env(engine: "DataEngine") -> asyncio.Server:
    """
    从 .env 文件读取 TCP_HOST / TCP_PORT 并启动 TCP 消费者。
    如果未配置，使用默认值 127.0.0.1:9000。
    """
    host = os.getenv("TCP_HOST", "127.0.0.1")
    port = int(os.getenv("TCP_PORT", "9000"))
    return await start_tcp_consumer(engine, host, port)
