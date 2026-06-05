"""
test_iec61850_gateway.py — IEC 61850 网关仿真器

模拟"C 网关进程"通过 TCP 向后端发送已解析的 IEC 61850 数据对象。

在真实生产环境中：
  IED ──IEC 61850 MMS──→ 网关(C) ──JSON over TCP──→ Python FastAPI 后端

本仿真器模拟"网关 → 后端"这一段：
  1. 读取 DATA_POINT_DEFS 中定义的 DO ref 列表
  2. 在默认值上叠加 ±5% 随机波动
  3. 构造 iec61850_raw 格式的 JSON 报文
  4. 通过 TCP 发送到后端（Line-delimited JSON）

数据流：
  本仿真器 ──TCP:9000──→ tcp_server.py ──→ Chart4Transformer ──→ frontend

使用方法：
  # 先确保后端已启动：
  cd server
  python -m uvicorn src.main:app --reload --port 8000

  # 然后运行本仿真器：
  python tests/test_iec61850_gateway.py

  # 自定义参数：
  python tests/test_iec61850_gateway.py --interval 2 --port 9000

预期行为：
  - 后端日志显示收到 iec61850_raw 消息，transformer 输出 Chart4Payload
  - 前端 Chart4 折线图、收益总计、企业数量每 N 秒更新
  - 如果旧仿真器 test_tcp_client.py 同时运行，两种消息格式互不干扰
"""

import asyncio
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════
# 确保可以从 server/ 目录运行
# ══════════════════════════════════════════════════════════════════════════
_server_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_server_root))

from src.iec61850.config import DATA_POINT_DEFS


# ══════════════════════════════════════════════════════════════════════════
# 报文生成
# ══════════════════════════════════════════════════════════════════════════

def generate_data_points() -> list[dict]:
    """
    生成一批 IEC 61850 数据对象（模拟一个数据报告周期）。

    为了让前端明显看出数据在变化，采用大幅随机波动（30%~300% 范围），
    真实生产环境中应改回 ±5% 的自然波动。

    返回:
        list[dict]: 每个元素包含 ref / value / quality / timestamp
    """
    data_points: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()

    for dp_def in DATA_POINT_DEFS:
        # ── 大幅随机：0.3x ~ 3.0x（让前端数字剧烈跳动，肉眼可见） ──
        factor = random.uniform(0.3, 3.0)

        if dp_def.ref in ("MMTR1.TotWh.act", "GGIO1.IntIn1.stVal"):
            value = round(dp_def.default * factor)
        else:
            value = round(dp_def.default * factor, 2)

        data_points.append({
            "ref": dp_def.ref,
            "value": value,
            "quality": "0x0000",
            "timestamp": now,
        })

    return data_points


def generate_message(device: str) -> dict:
    """
    生成一条完整的网关报文。

    参数:
        device: IED 标识符，如 "SB1_IED1"（变电站1  IED1）

    返回:
        dict: 完整的 iec61850_raw 格式报文
    """
    return {
        "type": "iec61850_raw",
        "device": device,
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "data_points": generate_data_points(),
    }


# ══════════════════════════════════════════════════════════════════════════
# 主循环
# ══════════════════════════════════════════════════════════════════════════

async def run_simulator(
    host: str = "127.0.0.1",
    port: int = 9000,
    interval: float = 3.0,
    device: str = "SB1_IED1",
):
    """
    运行网关仿真器主循环。

    参数:
        host:     后端 TCP Server 地址
        port:     后端 TCP Server 端口
        interval: 发送间隔（秒）
        device:   模拟的 IED 标识符
    """
    print("=" * 60)
    print("🔌 IEC 61850 网关仿真器 v0.1")
    print(f"   目标:    tcp://{host}:{port}")
    print(f"   间隔:    {interval} 秒/次")
    print(f"   设备:    {device}")
    print(f"   数据对象: {len(DATA_POINT_DEFS)} 个 DO ref（±5% 随机波动）")
    print("=" * 60)
    print()
    print("   DO ref 清单:")
    for dp in DATA_POINT_DEFS:
        print(f"     {dp.ref:<40} {dp.label:<12} (默认: {dp.default} {dp.unit})")
    print()
    print("   数据流: 本仿真器 ──TCP──→ tcp_server.py ──→ Chart4Transformer ──→ 前端")
    print("=" * 60)
    print()

    # ── 连接到后端 TCP Server ──
    try:
        reader, writer = await asyncio.open_connection(host, port)
        print(f"✅ 已连接到后端: {host}:{port}\n")
    except ConnectionRefusedError:
        print(f"❌ 无法连接到 {host}:{port}")
        print("   请先启动后端服务:")
        print("   cd server && python -m uvicorn src.main:app --reload --port 8000")
        return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    send_count = 0

    try:
        while True:
            # 生成一条带随机波动的网关报文
            message = generate_message(device)

            # JSON → bytes + 换行符分隔
            data_str = json.dumps(message, ensure_ascii=False) + "\n"
            data_bytes = data_str.encode("utf-8")

            writer.write(data_bytes)
            await writer.drain()

            send_count += 1
            timestamp = message["timestamp"]
            dps = message["data_points"]

            print(f"[{timestamp}] 📤 第 {send_count} 次发送:")
            print(f"   消息类型: {message['type']}")
            print(f"   设备标识: {message['device']}")
            print(f"   数据对象: {len(dps)} 个")
            for dp in dps[:3]:  # 只打印前 3 个做示例
                print(f"     {dp['ref']:<40} = {dp['value']}")
            if len(dps) > 3:
                print(f"     ... 还有 {len(dps) - 3} 个")
            print()

            await asyncio.sleep(interval)

    except ConnectionResetError:
        print(f"\n📴 连接被后端关闭（共发送 {send_count} 次）")
    except KeyboardInterrupt:
        print(f"\n\n👋 用户中断，仿真器停止（共发送 {send_count} 次）")
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
            print("🔒 TCP 连接已关闭")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════
# 命令行入口
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="IEC 61850 网关仿真器 — 模拟 C 网关向后端发送已解析的数据对象"
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
    parser.add_argument(
        "--device",
        default="SB1_IED1",
        help="模拟的 IED 标识符（默认: SB1_IED1）",
    )

    args = parser.parse_args()
    asyncio.run(run_simulator(args.host, args.port, args.interval, args.device))
