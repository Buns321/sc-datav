# sc-datav 后端服务

> 写给嵌入式开发者的后端入门指南（你懂 STM32/C/电控，那就用这些类比）

---

## 这个后端是干什么的？

这个 Python 程序同时启动**两个网络服务**：

| 服务 | 端口 | 协议 | 作用 |
|------|------|------|------|
| **WebSocket Server** | 8000 | WebSocket | 给浏览器前端推送数据 |
| **TCP Server** | 9000 | 原始 TCP | 接收"上位机"发来的数据报文 |

相当于一个**翻译官**：把工厂设备的 TCP 报文翻译成浏览器能懂的 WebSocket 消息。

```
上位机（工厂采集系统）
    │
    │  原始 TCP 报文（JSON over TCP）
    │  tcp://localhost:9000
    ▼
┌──────────────────────┐
│  sc-datav 后端服务    │
│  Python FastAPI      │
├──────────────────────┤
│  接收 → 校验 → 广播   │
└──────────────────────┘
    │
    │  WebSocket 推送
    │  ws://localhost:8000/ws
    ▼
浏览器大屏前端
```

---

## 项目结构速览

```
server/
├── README.md                  ← 你正在看的文件
├── pyproject.toml             ← Python 项目配置（类似 C 的 CMakeLists.txt / Makefile）
├── .env                       ← 环境变量（端口号等，类似 .env 配置文件）
├── src/
│   ├── __init__.py            ← 声明"这是一个 Python 包"
│   ├── main.py                ← 🎯 入口：启动 FastAPI + TCP Server（类似 main.c）
│   ├── tcp_server.py          ← TCP Server（接收上位机，类似 UART 接收中断服务函数）
│   ├── ws_manager.py          ← WebSocket 连接管理器（类似 DMA 的多通道管理）
│   ├── models/
│   │   └── chart4.py          ← Chart4 数据格式定义（类似 struct 定义）
│   └── data/
│       └── chart4_data.py     ← Chart4 数据存储（"内存数据库"，类似全局变量 buffer）
└── tests/
    └── test_tcp_client.py     ← 🎮 上位机模拟器（类似串口调试助手）
```

| 文件 | 一句话说明 |
|------|-----------|
| `main.py` | 程序入口，启动 FastAPI（Web 框架）和 TCP Server，类似 `int main()` |
| `tcp_server.py` | 开一个 TCP 端口（9000），等待上位机连接并接收数据，类似 UART RX 中断 |
| `ws_manager.py` | 管理所有浏览器 WebSocket 连接，向它们广播消息，类似 DMA 多通道分发 |
| `models/chart4.py` | 用 Pydantic 定义"Chart4 数据应该长什么样"，类似 struct + 数据校验 |
| `data/chart4_data.py` | 在内存中存 Chart4 的当前数据，类似一个全局 `static` 变量 buffer |
| `test_tcp_client.py` | 模拟上位机发出带随机波动的 Chart4 数据，类似串口调试助手发测试报文 |

---

## 快速开始

### 第一步：安装依赖

```bash
cd server

# 如果还没有安装，在项目根目录运行：
pip install fastapi uvicorn pydantic python-dotenv
```

这些包的作用（类比 STM32 的 HAL 库）:

| 包名 | 作用 | 单片机类比 |
|------|------|-----------|
| `fastapi` | Web 框架（路由、WebSocket） | 类似 HAL 库的框架层，提供了各种封装好的接口 |
| `uvicorn` | 运行 FastAPI 的服务器 | 类似调试下载器（ST-Link），让程序跑起来 |
| `pydantic` | 数据校验 | 类似 assert / 数据帧 CRC 校验 |
| `python-dotenv` | 读 `.env` 文件 | 类似 Keil 的预定义宏，编译时读配置 |
| `websockets` | WebSocket 协议支持 | 类似 TCP/IP 协议栈的移植层 |

### 第二步：启动后端

```bash
# 在 server/ 目录下运行
cd server
python -m uvicorn src.main:app --reload --port 8000
```

看到以下输出说明启动成功：

```
🚀 sc-datav 后端服务启动中...
🚀 TCP Server 已启动: tcp://127.0.0.1:9000
✅ WebSocket 端点: ws://localhost:8000/ws
✅ TCP 数据端口: tcp://localhost:9000
```

> 🔧 **`--reload` 参数**：文件修改后自动重启（类似 Vite 的 HMR）。开发时强烈建议加这个参数。

### 第三步：运行上位机模拟器

在**另一个终端**中：

```bash
cd server
python tests/test_tcp_client.py
```

你会看到类似输出：

```
🔌 上位机模拟器 v0.1
✅ 已连接到后端: 127.0.0.1:9000

[12:00:00] 📤 第 1 次发送:
   折线数据: [283, 412, 390, 435, 308, 422, 415, 340, 216, 298]
   收益总计: 101,234 亿元
   企业数量: 7,890 个
```

### 第四步：启动前端

在**项目根目录**的第三个终端：

```bash
pnpm dev
```

打开浏览器访问 DataCenter 页面，**Chart4 的数字会每隔几秒跳动一次**。

---

## 写给嵌入式开发者的后端术语表（用你懂的做类比）

| 术语 | 含义 | 嵌入式/电控类比 |
|------|------|----------------|
| **FastAPI** | Python 的 Web 框架 | 类似 STM32 HAL 库——提供封装好的接口，不用从寄存器层面开始写 |
| **uvicorn** | ASGI 服务器（运行 FastAPI） | 类似 ST-Link 调试器——让程序在硬件上跑起来 |
| **Pydantic** | 数据校验库 | 类似 `assert()` + 串口协议帧的 CRC 校验，确保收到的数据格式正确 |
| **asyncio** | Python 异步编程库 | 类似 RTOS 的任务调度——多个任务轮流执行，不阻塞 |
| **协程（Coroutine）** | async def 定义的函数 | 类似 RTOS 的一个任务（task）——可以被挂起和恢复 |
| **WebSocket** | 基于 TCP 的双向通信协议 | 类似一条"一直连着的串口"——双方随时可以发数据，不用反复打开关闭 |
| **TCP** | 传输层协议，保证数据可靠到达 | 类似 RS485 + Modbus 协议——保证数据包完整、不丢失、不乱序 |
| **Line-delimited JSON** | 每条 JSON 消息以换行符 `\\n` 分隔 | 类似串口协议中的帧头帧尾（`\\n` 就是帧尾标记） |
| **Lock（锁）** | 防止并发读写出错 | 类似 RTOS 中的互斥信号量（Mutex）——防止两个任务同时修改同一个全局变量 |
| **单例（Singleton）** | 全局唯一的实例 | 类似全局变量 + `static` 限制——整个程序只有一个实例 |

---

## 常见问题

### Q: 为什么需要两个端口（8000 和 9000）？

浏览器只能用 WebSocket 协议（端口 8000），但真实的工业上位机往往只支持原始 TCP（端口 9000）。

这就像你的 STM32 通过串口发数据给电脑，电脑再通过 USB 转 Ethernet 转发到服务器。单片机不需要关心上层协议是什么，它只管发原始字节。

### Q: 后端启动报 `ModuleNotFoundError: No module named 'src'`？

确保在 `server/` 目录下运行命令：
```bash
cd server
python -m uvicorn src.main:app --reload --port 8000
```

这就像 IAR 的工程文件必须在工程目录下打开一样，Python 需要找到正确的文件路径。

### Q: 上位机模拟器报 `ConnectionRefusedError`？

说明后端还没启动，或者后端没有正确启动 TCP Server。先启动后端再看日志。

就像你用串口调试助手时，得先把单片机的串口初始化好，调试助手才能连上。

### Q: 数据存在哪里？重启后还在吗？

目前数据存在**内存里**（Python 变量），重启后就丢了。这跟你 STM32 的全局变量一样——断电重启就回到初始值。后续会接入真正的数据库。

### Q: 为什么用 asyncio 而不是 threading？

FastAPI 本身就是异步（async）的。用 asyncio 启动 TCP Server 可以和 FastAPI 共享同一个事件循环，不需要处理多线程的并发问题。

类比 RTOS：asyncio 像是在一个单核 MCU 上跑 RTOS——所有任务共享一个 CPU，通过协作式调度切换。threading 则像是多核 MCU——每个核各自跑各自的，需要考虑资源竞争和锁的问题。明显单核 + 协作式调度更简单。
