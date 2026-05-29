"""
test_tcp_client.py — 上位机模拟器

这个脚本模拟"工厂上位机"通过原始 TCP 向后端发送数据。

🔧 写给嵌入式开发者的上下文：

在真实的工业/物联网场景中：
  - 下位机（PLC/传感器）采集数据 → 发给上位机
  - 上位机（监控电脑/边缘计算节点）汇总数据 → 发给后端服务器
  - 后端服务器处理数据 → 推送给大屏前端

本模拟器扮演"上位机"角色：
  1. 每 N 秒自动生成一段 Chart4 数据（模拟"传感器采集"）
  2. 在默认值上叠加 ±5% 随机波动（模拟"真实数据波动"）
  3. 通过原始 TCP 发送给后端（模拟"上位机上报"）

使用方法：
  # 先确保后端已启动（在另一个终端）：
  cd server
  python -m uvicorn src.main:app --reload --port 8000

  # 然后运行模拟器：
  python tests/test_tcp_client.py

  # 或自定义间隔（每 2 秒发一次）：
  python tests/test_tcp_client.py --interval 2

  # 或自定义端口：
  python tests/test_tcp_client.py --port 9000 --interval 5

预期输出：
  [12:00:00] 📤 发送: {"type":"chart4_update","payload":{"line_data":[283,412,...],"total_revenue":101234,"enterprise_count":7890},...}
  [12:00:03] 📤 发送: {"type":"chart4_update","payload":{"line_data":[258,389,...],"total_revenue":98012,"enterprise_count":7654},...}
  ...

然后在浏览器中打开 DataCenter 页面，Chart4 的数字会每几秒跳动一次。
"""

import asyncio
import json
import random
import time
from datetime import datetime, timezone


# ============================================================================
# 默认数据 —— 与后端 chart4_data.py 和前端 chart4.tsx 一致
# ============================================================================

DEFAULT_CHART4_DATA: dict = {
    "line_data": [270, 400, 380, 420, 300, 410, 400, 330, 210, 290],
    "total_revenue": 99608,   # 收益总计（亿元）
    "enterprise_count": 7792,  # 企业数量（个）
}


def generate_variation() -> dict:
    """
    在默认数据上叠加 ±5% 的随机波动，生成一条模拟报文。

    🔧 为什么要有随机波动？
    真实的上位机数据不是固定不变的——会有微小的上下浮动。
    加上随机波动能让模拟的数据看起来更"真实"，
    用户体验更好的同时也有利于验证前端的"数据变化检测"机制。

    返回:
        dict: 包含 type, timestamp, payload 的完整报文
    """
    # 生成随机因子：0.95 ~ 1.05（即 ±5%）
    factor = random.uniform(0.95, 1.05)

    # 🔧 Python 的列表推导式（list comprehension）：
    # [表达式 for 变量 in 列表] = JavaScript 的 arr.map(v => 表达式)
    # 下面的代码等价于 JS 的：
    #   line_data.map(v => Math.max(50, Math.round(v * Math.random() * 0.1 + 0.95 * v)))
    varied_line_data = [
        max(50, round(v * random.uniform(0.95, 1.05)))
        for v in DEFAULT_CHART4_DATA["line_data"]
    ]

    # 收益总计：加随机波动
    varied_revenue = round(DEFAULT_CHART4_DATA["total_revenue"] * factor)

    # 企业数量：加随机波动
    varied_count = round(DEFAULT_CHART4_DATA["enterprise_count"] * factor)

    # 构造报文
    return {
        "type": "chart4_update",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "payload": {
            "line_data": varied_line_data,
            "total_revenue": varied_revenue,
            "enterprise_count": varied_count,
        },
    }


async def run_simulator(host: str = "127.0.0.1", port: int = 9000, interval: float = 3.0):
    """
    运行上位机模拟器的主循环

    参数:
        host: 后端 TCP Server 的 IP 地址
        port: 后端 TCP Server 的端口
        interval: 发送间隔（秒），默认 3 秒

    流程:
        1. 连接后端的 TCP Server
        2. 无限循环：生成数据 → 发送 → 等待 interval 秒
    """
    print("=" * 60)
    print("🔌 上位机模拟器 v0.1")
    print(f"   目标: tcp://{host}:{port}")
    print(f"   间隔: {interval} 秒/次")
    print(f"   数据: Chart4 企业收益统计（±5% 随机波动）")
    print("=" * 60)

    # ================================================================
    # 步骤 1：连接后端 TCP Server
    # ================================================================
    # 🔧 asyncio.open_connection(host, port)
    # 打开一个 TCP 连接到指定地址。
    # 返回 reader（读）和 writer（写），和 tcp_server.py 中的 handle_client 对应。
    # 类比：前端的 new WebSocket("ws://localhost:8000/ws")
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print(f"✅ 已连接到后端: {host}:{port}\n")
    except ConnectionRefusedError:
        # 🔧 ConnectionRefusedError = "连接被拒绝"
        # 原因：目标端口上没有服务在监听
        # 解决方法：先启动后端（uvicorn ...）
        print(f"❌ 无法连接到 {host}:{port}")
        print("   请先启动后端服务:")
        print("   cd server && python -m uvicorn src.main:app --reload --port 8000")
        return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    # 统计发送次数
    send_count = 0

    try:
        # ================================================================
        # 步骤 2：无限循环 —— 定时生成并发送数据
        # ================================================================
        while True:
            # 生成一条带随机波动的数据
            message = generate_variation()

            # ============================================================
            # 把 Python 字典转成 JSON 字符串，然后编码为字节
            #
            # 🔧 网络传输必须用字节（bytes），不能用字符串（str）
            # json.dumps() = JSON.stringify()
            # .encode("utf-8")  = 把字符串转成字节（类似 TextEncoder）
            # 末尾加 \\n = 换行符（Line-delimited JSON 的分隔符）
            # ============================================================
            data_str = json.dumps(message) + "\n"
            data_bytes = data_str.encode("utf-8")

            # 发送数据
            writer.write(data_bytes)
            # 🔧 await writer.drain()
            # 等待操作系统把数据真正发送出去（排空写入缓冲区）
            # 类比：前端的 await fetch() 等响应
            await writer.drain()

            send_count += 1
            timestamp = message["timestamp"]

            # 格式化输出（方便查看）
            print(f"[{timestamp}] 📤 第 {send_count} 次发送:")
            print(f"   折线数据: {message['payload']['line_data']}")
            print(f"   收益总计: {message['payload']['total_revenue']:,} 亿元")
            print(f"   企业数量: {message['payload']['enterprise_count']:,} 个")
            print()

            # ============================================================
            # 等待 interval 秒后再发下一次
            # 🔧 asyncio.sleep() = 异步的 setTimeout
            # 不会阻塞整个程序（如果有其他协程，它们可以继续运行）
            # ============================================================
            await asyncio.sleep(interval)

    except ConnectionResetError:
        # 后端关闭了连接
        print(f"\n📴 连接被后端关闭（共发送 {send_count} 次）")
    except KeyboardInterrupt:
        # 🔧 KeyboardInterrupt = 用户按下了 Ctrl+C
        # 优雅退出：关闭连接，打印统计
        print(f"\n\n👋 用户中断，模拟器停止（共发送 {send_count} 次）")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    finally:
        # ================================================================
        # 清理：关闭 TCP 连接
        # ================================================================
        try:
            writer.close()
            await writer.wait_closed()
            print("🔒 TCP 连接已关闭")
        except Exception:
            pass  # 连接可能已经断了，忽略关闭时的错误


# ============================================================================
# 命令行入口
#
# 🔧 if __name__ == "__main__" 的作用：
# 当这个文件被直接执行（python test_tcp_client.py）时，运行下面的代码。
# 当这个文件被其他文件 import 时，不运行（只导入函数定义）。
#
# 类比：Node.js 的 if (require.main === module) { ... }
# ============================================================================

if __name__ == "__main__":
    import argparse

    # 🔧 argparse 是 Python 的命令行参数解析库
    # 让你可以用 --interval 2 这样的方式传参数
    # 类比：Node.js 的 commander 或 yargs 包
    parser = argparse.ArgumentParser(
        description="上位机模拟器 — 通过 TCP 向后端发送模拟 Chart4 数据"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="后端 TCP Server 地址（默认: 127.0.0.1）",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9000,
        help="后端 TCP Server 端口（默认: 9000）",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=3.0,
        help="发送间隔，单位秒（默认: 3.0）",
    )

    args = parser.parse_args()

    # 🔧 asyncio.run() 启动异步程序的主入口
    # 这是 Python 异步程序的标准启动方式
    # 类比：JavaScript 中直接 await（顶层 await）
    asyncio.run(run_simulator(args.host, args.port, args.interval))
