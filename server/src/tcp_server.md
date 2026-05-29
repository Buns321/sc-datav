# 理解 TCP Server — 写给嵌入式开发者

> 📖 配套阅读：`server/src/tcp_server.py` 源码（包含大量行内注释）

---

## TCP 是什么？

**TCP（传输控制协议）** 和串口非常像。如果你写过 STM32 的 UART 通信，下面的对比会让你秒懂：

| 概念 | UART 串口 | TCP |
|------|-----------|-----|
| 连接 | TX 接 RX，物理线缆 | IP 地址 + 端口，网络连接 |
| 数据传输 | 发送字节流 | 发送字节流 |
| 帧格式 | 自己定（帧头+数据+校验+帧尾） | 内置（序列号+校验+重传） |
| 可靠性 | 取决于物理连接质量 | 内置确认重传机制（可靠） |
| 双工 | 全双工（TX/RX 同时） | 全双工 |

**和串口的核心区别**：TCP 内置了"可靠传输"机制——如果数据包丢了，TCP 会自动重发，不需要你在应用层做校验。

---

## TCP 与 WebSocket 的层次关系

```
┌─────────────────────────────────────┐
│  应用层（你的业务数据）              │
│  {"type":"chart4_update", ...}      │
├─────────────────────────────────────┤
│  WebSocket 协议层                   │  ← 类似 Modbus 协议（在原始字节流上加帧格式）
│  规定了握手、数据封帧格式            │
├─────────────────────────────────────┤
│  TCP 传输层                         │  ← 类似串口物理层，但自带可靠性
│  保证数据不丢、不乱序               │
├─────────────────────────────────────┤
│  IP 网络层 + 物理层（网线/WiFi）    │  ← 类似 RS485 总线
└─────────────────────────────────────┘
```

**核心区别**：
- **TCP** = 串口物理层（传输原始字节流，但自带可靠性）
- **WebSocket** = 在 TCP 之上加了"协议帧格式"（类似 Modbus RTU 在串口上加了帧格式）
- 浏览器只支持 WebSocket（没有原始 TCP API）

---

## 为什么本项目需要 TCP Server？

在真实的工业/物联网场景中：

```
PLC/传感器 (下位机)
    ↓
上位机（监控电脑，汇总所有传感器数据）
    ↓  通常只支持原始 TCP 报文
后端服务器  ← 我们需要接收这部分数据
    ↓  转成 WebSocket
浏览器大屏
```

上位机（工厂的监控电脑）发送的报文通常是**原始 TCP + 自定义协议**（常见格式有 Modbus TCP、自定义 JSON over TCP 等）。

本项目的 TCP Server 就是为了**接收这些原始报文**，然后把数据"翻译"给前端。

这就像你 STM32 通过串口接收传感器数据，再通过另一个串口转发给上位机。这里只是把"另一个串口"换成了 WebSocket。

---

## 数据协议：Line-delimited JSON

本项目使用 **Line-delimited JSON**（NDJSON）格式：

```
每条消息 = 一行完整的 JSON + 换行符 \n
```

例如上位机发送：
```
{"type":"chart4_update","timestamp":"2026-05-28T12:00:00Z","payload":{...}}\n
{"type":"chart4_update","timestamp":"2026-05-28T12:00:03Z","payload":{...}}\n
```

> 🔧 为什么用换行符分隔？
> TCP 是**流式传输**——数据像水流一样连续到达，没有"消息边界"。
> 接收端不知道一条消息在哪里结束、下一条在哪里开始。
> 用换行符作为分隔符是**最简单可靠**的方案，就像串口协议中常用 0x0A 0x0D（CR/LF）做帧尾。

---

## asyncio 是什么？

`asyncio` 是 Python 的**异步编程库**，如果你写过 RTOS（FreeRTOS / RT-Thread），你会发现它非常眼熟：

| RTOS 概念 | Python asyncio |
|-----------|----------------|
| 任务（Task） | 协程（Coroutine），`async def` 定义的函数 |
| 任务调度 | 事件循环（Event Loop） |
| `osDelay(ms)` | `asyncio.sleep(seconds)` |
| 信号量 / 互斥锁 | `asyncio.Lock` |
| 消息队列 | `asyncio.Queue` |

**为什么用 asyncio 而不是多线程？**

就像一个单核 MCU 跑 RTOS——所有任务共享一个 CPU，通过协作式调度切换，不需要考虑复杂的资源竞争问题。

asyncio 也是一样：它只有一个线程，通过"协程"在任务之间切换，比多线程简单得多，也不容易出现死锁、竞态等问题。

---

## 数据流全貌

```
1. 上位机模拟器:
   test_tcp_client.py
   → 生成带随机波动的 Chart4 数据
   → writer.write(JSON + "\n")
   → 原始 TCP → localhost:9000

2. 后端 TCP Server:
   tcp_server.py → handle_client()
   → reader.readline()      ← 逐行读取（类似 UART 接收中断逐字节接收）
   → json.loads()           ← 解析 JSON（类似解析 Modbus 帧）
   → update_data()          ← 更新内存中的"全局变量 buffer"
   → ws_manager.broadcast() ← 转发给所有浏览器连接

3. 浏览器前端:
   demo.tsx
   → WebSocket 收到 JSON
   → 存入 dataStore
   → Chart4 组件重新渲染
```
