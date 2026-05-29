"""
main.py — 应用入口文件

这个文件是后端的"大门"（类似前端的 App.tsx / main.tsx）。
它负责：
  1. 创建 FastAPI 应用（Web 框架的"根组件"）
  2. 注册 WebSocket 路由（有人连接 /ws 时怎么办）
  3. 在启动时同时开启 TCP Server（一个"副业"）
  4. 在关闭时清理所有连接

🔧 写给嵌入式开发者的快速理解：

把 FastAPI 想象成 STM32 的 HAL 库：
  - HAL_GPIO_WritePin()       → FastAPI 的 @app.get("/api")
  - 烧录程序到芯片并复位启动  → uvicorn.run(app, port=8000)
  - 串口中断接收回调          → WebSocket 的 receive_text()

运行方式：
  # 开发模式（代码改了自动重启）
  uvicorn src.main:app --reload --port 8000

  # 或直接在项目根目录运行
  cd server
  python -m uvicorn src.main:app --reload --port 8000

🔧 uvicorn 是什么？
  uvicorn 是 Python 的 ASGI 服务器（类似 Vite 的 dev server）。
  - --reload：文件改动后自动重启（类似 Vite 的 HMR）
  - --port：指定监听端口

🔧 "src.main:app" 的含义：
  - src.main = src/main.py 文件
  - :app    = 文件中的 app 变量（即 FastAPI() 实例）
  这是一种"告诉 uvicorn 去哪里找应用"的标准写法。
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

# 导入我们自己写的模块
from src.ws_manager import manager as ws_manager
from src.tcp_server import start_tcp_from_env
from src.data.chart4_data import get_current_data

# 加载 .env 环境变量
load_dotenv()

# ============================================================================
# 日志配置
# 🔧 logging 是 Python 内置的日志模块，类似前端的 console.log
# 但更强大：可以控制级别、输出到文件、带时间戳等
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ============================================================================
# TCP Server 的引用
# 需要在应用启动/关闭时访问，所以声明为全局变量
# ============================================================================
_tcp_server: asyncio.Server | None = None  # 🔧 Type | None = TypeScript 的 Type | null


# ============================================================================
# 应用生命周期管理
#
# 🔧 @asynccontextmanager 是什么？
# 这是 Python 的上下文管理器（context manager），用于管理资源的"开启"和"关闭"。
#
# 类比：React useEffect 的 return cleanup 函数
#   yield 之前 = useEffect(() => { ... 副作用代码 ...
#   yield 之后 = ... return () => { ... 清理代码 ... } }, [])
#
# FastAPI 用 lifespan 来管理"应用启动时做什么"和"应用关闭时做什么"。
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理器

    负责：
      - 应用启动时：启动 TCP Server
      - 应用关闭时：关闭 TCP Server
    """
    global _tcp_server

    # ====== 启动阶段（类似 useEffect 的函数体） ======
    logger.info("=" * 50)
    logger.info("🚀 sc-datav 后端服务启动中...")
    logger.info("=" * 50)

    # 启动 TCP Server（接收上位机的数据）
    _tcp_server = await start_tcp_from_env()

    logger.info(f"✅ WebSocket 端点: ws://localhost:{os.getenv('FASTAPI_PORT', '8000')}/ws")
    logger.info(f"✅ TCP 数据端口: tcp://localhost:{os.getenv('TCP_PORT', '9000')}")
    logger.info("=" * 50)

    yield  # ← 这里是"分界线"，以上是启动，以下是关闭

    # ====== 关闭阶段（类似 useEffect 的 return cleanup） ======
    logger.info("🛑 sc-datav 后端服务关闭中...")

    if _tcp_server:
        # 关闭 TCP Server，不再接受新连接
        _tcp_server.close()
        # 等待所有现有连接处理完毕
        await _tcp_server.wait_closed()
        logger.info("✅ TCP Server 已关闭")

    logger.info("👋 服务已完全关闭")


# ============================================================================
# 创建 FastAPI 应用
#
# 🔧 FastAPI() 创建一个应用实例。
# 这个 app 对象就是后续所有路由、中间件的"注册中心"。
# 类比：Express 的 const app = express()
# ============================================================================
app = FastAPI(
    title="sc-datav 后端服务",
    description="数据可视化大屏后端 — 接收上位机 TCP 报文，通过 WebSocket 推送给前端",
    version="0.1.0",
    lifespan=lifespan,  # 注册生命周期管理器
)


# ============================================================================
# WebSocket 路由
#
# 🔧 @app.websocket("/ws")
# 这行代码的意思是："如果有人访问 /ws 路径，而且是用 WebSocket 协议，
# 就调用下面这个函数处理它"。
#
# 类比：Express 的
#   app.ws("/ws", (ws, req) => { ... })  // 需要 express-ws 包
#
# FastAPI 内置支持 WebSocket，不需要额外安装包。
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点 —— 浏览器前端连接到这里

    当浏览器打开 DataCenter 页面，前端 WSClient 会连接 ws://localhost:8000/ws，
    FastAPI 收到连接后调用这个函数。

    参数:
        websocket: FastAPI 注入的 WebSocket 对象，代表这一条浏览器连接

    流程:
        1. 接受连接（加入管理器）
        2. 发送当前已有数据（让前端立即看到）
        3. 保持连接，等待前端发消息（或直到连接断开）
        4. 连接断开时清理
    """
    # 步骤 1：接受连接，注册到管理器
    await ws_manager.connect(websocket)

    try:
        # 步骤 2：连接成功后，立即推送当前 Chart4 数据
        # 这样前端打开页面时不用等待上位机发数据，
        # 直接就能看到上一次的数据（或默认值）
        current_data = await get_current_data()
        initial_msg = {
            "type": "data",
            "channel": "chart4",
            "payload": current_data,
            "timestamp": "",
        }
        await websocket.send_json(initial_msg)
        logger.info(f"📤 已向新连接发送当前 Chart4 数据")

        # 步骤 3：进入消息循环 —— 等待前端发来消息
        # 🔧 这是一个无限循环，只要连接不断开就一直运行
        # 当客户端断开连接时，receive_text() 会抛出 WebSocketDisconnect 异常
        while True:
            # 等待前端发来一条文本消息
            # 🔧 receive_text() = 等待并接收一条文本消息
            # 如果前端不发消息，这里就一直等待（不消耗 CPU）
            data = await websocket.receive_text()

            # 🔧 当前阶段，前端可能不需要发送复杂指令
            # 这里预留了消息处理逻辑的扩展点
            # 后续如果需要前端向后端发指令（比如切换数据源），在这里扩展
            logger.debug(f"📨 收到前端消息: {data}")

    except WebSocketDisconnect:
        # 🔧 WebSocketDisconnect 是 FastAPI 提供的异常
        # 当浏览器关闭页面或断网时，receive_text() 会抛出这个异常
        logger.info("🔌 前端 WebSocket 断开连接")
    except Exception as e:
        # 其他未预期的错误
        logger.error(f"❌ WebSocket 处理出错: {e}")
    finally:
        # 无论如何，断开连接时都要从管理器中移除
        await ws_manager.disconnect(websocket)


# ============================================================================
# 健康检查端点（可选但推荐）
# 用于确认服务是否在运行
# ============================================================================

@app.get("/health")
async def health_check():
    """
    健康检查端点

    访问 http://localhost:8000/health 查看服务是否正常运行。

    返回当前 WebSocket 连接数等基本信息。
    类似前端的"ping"接口，用来确认服务还活着。
    """
    return {
        "status": "ok",
        "service": "sc-datav-server",
        "ws_connections": ws_manager.connection_count,
        "tcp_server": "running" if _tcp_server and _tcp_server.is_serving() else "stopped",
    }


# ============================================================================
# 直接运行入口（开发调试用）
#
# 如果直接执行 `python main.py`（而不是通过 uvicorn），
# 这个 if 块会启动服务。
# ============================================================================

if __name__ == "__main__":
    # 🔧 这种方式只适合开发调试，生产环境应该用 uvicorn 命令行
    import uvicorn

    port = int(os.getenv("FASTAPI_PORT", "8000"))
    uvicorn.run("src.main:app", host="127.0.0.1", port=port, reload=True)
