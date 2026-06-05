"""
tcp_server.py — 原始 TCP 服务器

这个模块启动一个 TCP Socket 服务器，接收"上位机"通过原始 TCP 发来的数据。

🔧 写给嵌入式开发者 —— TCP 和串口的类比：

如果你写过 STM32 的串口通信，那你已经懂 TCP 了：

  UART 串口：    TX ——RX  点对点，发送字节流
  TCP 网络：     本地端口 —— 远程端口  点对点，发送字节流
  WebSocket：    在 TCP 之上加了"协议封装"（类似 Modbus 协议在串口之上封装了帧格式）

  区别只是：UART 用物理线缆连接，TCP 用网络连接。

  本项目的 TCP Server = 一个永不停歇的串口接收中断：
  - reader.readline()  ≈  UART 中断服务函数中逐个字节接收
  - json.loads()       ≈  解析 Modbus 协议帧
  - broadcast()        ≈  把解析后的数据通过另一个通道转发出去

为什么本项目需要两个服务器（TCP + WebSocket）？
  - 浏览器只能用 WebSocket（浏览器没有原始 TCP API）
  - 但真实工业上位机往往只支持原始 TCP 发报文
  - 所以后端扮演"翻译官"角色：
    上位机 ──TCP──→ 本服务器 ──WebSocket──→ 浏览器

Line-delimited JSON 协议说明：
  每条消息是完整的 JSON，以换行符 \\n 结尾。
  这样接收端可以按行读取，不需要复杂的"分包"逻辑。
  类比：每句话以句号结尾，你才知道一句话说完了。
"""

import asyncio
import json
import logging
import os
from dotenv import load_dotenv

# 导入数据层（存数据的"便签纸"）和 WebSocket 管理器（广播数据的"广播站"）
from src.data.chart4_data import update_data
from src.ws_manager import manager as ws_manager
from src.transformers.chart4_transformer import Chart4Transformer

# load_dotenv() 读取 .env 文件中的环境变量
# 类似前端 Vite 读取 .env 文件的过程
load_dotenv()

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# Transformer 实例 —— 每个 TCP 连接共享同一个 transformer 单例
# ══════════════════════════════════════════════════════════════════════════
_transformer = Chart4Transformer()


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    处理单个 TCP 客户端连接

    你可以把这个函数想象成"接电话"：
      - 每当有上位机连接上来，这个函数就被调用一次
      - 每个连接有自己独立的 reader（听筒）和 writer（话筒）

    参数:
        reader: asyncio.StreamReader — "听筒"，用来读取客户端发来的数据
        writer: asyncio.StreamWriter — "话筒"，用来向客户端回复数据
               （本项目中我们一般不回复，只接收）

    🔧 关于 asyncio.StreamReader/StreamWriter：
    它们是 asyncio 对"原始字节流"的封装。
    类比：TCP 给了你一根水管（管道），reader 让你从水管里接水（读数据），
         writer 让你往水管里注水（写数据）。
    """

    # 获取客户端的 IP 地址，用于日志记录（只是记录，不影响功能）
    # 🔧 writer.get_extra_info('peername') 获取对方的地址
    # 'peername' = peer name = 对方的网络标识
    client_addr = writer.get_extra_info("peername")
    logger.info(f"📥 TCP 新连接接入: {client_addr}")

    try:
        # 🔧 reader.readline() 逐行读取数据
        # 每次读到 \\n 为止，返回的是一行文本（bytes 类型）
        # 如果客户端断开连接，返回空 bytes（b""）
        # 类比：前端的 ReadableStream 逐行读取
        while True:
            # 等待客户端发来一行数据
            line_bytes = await reader.readline()

            # 如果读到空数据，说明客户端主动断开了连接
            if not line_bytes:
                logger.info(f"📴 TCP 客户端断开: {client_addr}")
                break

            # ================================================================
            # 步骤 1：解码 bytes → 字符串
            # ================================================================
            # 🔧 网络传输的都是字节（bytes），需要解码成字符串
            # decode("utf-8") 类似 JavaScript 的 TextDecoder
            # strip() 去掉首尾空白字符（包括换行符）
            line_str = line_bytes.decode("utf-8").strip()

            # 跳过空行（有些客户端可能发空行）
            if not line_str:
                continue

            logger.debug(f"📨 收到原始报文 ({client_addr}): {line_str}")

            # ================================================================
            # 步骤 2：解析 JSON 字符串 → Python 字典
            # ================================================================
            # 🔧 json.loads() = JSON.parse()
            # 注意：和前端不同，Python 的 json.loads 不接受单引号的 JSON
            # 如果 JSON 格式不对，这里会抛 json.JSONDecodeError
            try:
                message = json.loads(line_str)
            except json.JSONDecodeError as e:
                logger.error(f"❌ 报文不是合法的 JSON ({client_addr}): {e}")
                continue  # 跳过这条错误消息，继续等待下一条

            # ================================================================
            # 步骤 3：提取公用字段并判断消息类型
            # ================================================================
            msg_type = message.get("type", "")
            payload = message.get("payload")
            timestamp = message.get("timestamp", "")

            # ── 分支 A: chart4_update（旧格式，调试用，直通存储） ──
            if msg_type == "chart4_update":
                # 验证 payload 是否存在
                if not payload:
                    logger.warning(f"⚠️ chart4_update 缺少 payload 字段 ({client_addr})")
                    continue

                logger.info(f"✅ [{msg_type}] 解析成功 ({client_addr}), 时间={timestamp}")

                # 直接存入数据层并广播
                await update_data(payload)

                broadcast_msg = {
                    "type": "data",
                    "channel": "chart4",
                    "payload": payload,
                    "timestamp": timestamp,
                }
                await ws_manager.broadcast(broadcast_msg)

            # ── 分支 B: iec61850_raw（新格式，生产用，走 transformer） ──
            elif msg_type == "iec61850_raw":
                data_points = message.get("data_points")
                if not data_points:
                    logger.warning(f"⚠️ iec61850_raw 缺少 data_points 字段 ({client_addr})")
                    continue

                device = message.get("device", "unknown")
                logger.info(
                    f"✅ [{msg_type}] 收到 {len(data_points)} 个数据对象 "
                    f"来自 {device} ({client_addr}), 时间={timestamp}"
                )

                # 喂入 transformer —— 累积到足够数据后才输出
                result = _transformer.feed(data_points)

                if result is not None:
                    # 数据到齐，存入数据层并广播
                    payload_dict = result.model_dump()
                    await update_data(payload_dict)

                    broadcast_msg = {
                        "type": "data",
                        "channel": "chart4",
                        "payload": payload_dict,
                        "timestamp": timestamp,
                    }
                    await ws_manager.broadcast(broadcast_msg)

            else:
                logger.warning(f"⚠️ 未知消息类型 ({client_addr}): {msg_type}")
                continue

    except ConnectionResetError:
        # 🔧 ConnectionResetError = 对方突然断开（类似"对方挂电话"）
        # 这是 TCP 通信中的正常现象，不需要 panic
        logger.info(f"📴 TCP 连接被重置: {client_addr}")
    except Exception as e:
        # 其他未知异常，记录日志但不崩溃
        logger.error(f"❌ TCP 处理出错 ({client_addr}): {e}")
    finally:
        # 🔧 finally 块中的代码无论如何都会执行（类似 JavaScript 的 finally）
        # 用于清理资源，比如关闭连接
        try:
            writer.close()
            # 🔧 await writer.wait_closed() = 等待连接完全关闭
            # 类比：挂电话后等待"嘟——"的确认音
            await writer.wait_closed()
        except Exception:
            pass  # 即使关闭时出错也忽略（连接可能已经断了）
        logger.info(f"🔒 TCP 连接已关闭: {client_addr}")


async def start_tcp_server(host: str = "127.0.0.1", port: int = 9000) -> asyncio.Server:
    """
    启动 TCP 服务器，等待上位机连接

    参数:
        host: 监听的 IP 地址
              "0.0.0.0" = 接受来自任何 IP 的连接（生产环境）
              "127.0.0.1" = 只接受本机的连接（开发环境，更安全）
        port: 监听的端口号，默认 9000

    返回:
        asyncio.Server 对象，可以用来停止服务器

    🔧 asyncio.start_server 的工作原理：
    1. 操作系统在指定端口上"监听"（类似开启一个电话总机）
    2. 每当有客户端连接上来，asyncio 就创建一个协程调用 handle_client
    3. 多个客户端可以同时连接，asyncio 在后台管理它们的并发
    不需要手动开线程——asyncio 用一个线程 + 事件循环就能处理成千上万个连接
    """
    # 🔧 asyncio.start_server(client_handler, host, port)
    # 参数 1: 处理每个连接的函数（handle_client）
    # 参数 2: 监听地址
    # 参数 3: 监听端口
    server = await asyncio.start_server(handle_client, host, port)

    # 获取服务器实际绑定的地址（在某些配置下可能和传入的不同）
    addr = server.sockets[0].getsockname() if server.sockets else (host, port)
    logger.info(f"🚀 TCP Server 已启动: tcp://{addr[0]}:{addr[1]}")
    logger.info(f"   等待上位机连接...")

    return server


# ============================================================================
# 便捷启动函数 — 从 .env 读取配置，自动启动 TCP Server
# ============================================================================

async def start_tcp_from_env() -> asyncio.Server:
    """
    从 .env 文件中读取 TCP_HOST 和 TCP_PORT 环境变量，启动 TCP 服务器。

    如果 .env 中没配置，使用默认值（127.0.0.1:9000）。

    返回:
        asyncio.Server 对象
    """
    host = os.getenv("TCP_HOST", "127.0.0.1")
    port = int(os.getenv("TCP_PORT", "9000"))
    return await start_tcp_server(host, port)
