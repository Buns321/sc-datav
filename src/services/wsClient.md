# WSClient API 文档

> 📖 配套阅读：`src/services/wsClient.ts` 源码（包含大量行内注释）

---

## 概述

`WSClient` 是浏览器的 WebSocket 客户端封装（单例模式），提供：

- 自动重连（指数退避，最多尝试 30 秒间隔）
- 心跳检测（30 秒间隔 Ping）
- 频道订阅管理（一个连接，多个数据频道）
- 连接状态暴露

---

## 数据流

```
Python 后端 (:8000/ws)
    │  WebSocket JSON 消息
    │  {"type":"data","channel":"chart4","payload":{...}}
    ▼
WSClient._handleMessage()
    │  解析 JSON，提取 channel
    ▼
_subscribers.get("chart4")
    │  遍历所有订阅者回调
    ▼
dataStore.set({ chart4: payload })
    │  Zustand 通知订阅者
    ▼
Chart4 组件重新渲染
```

---

## 使用方式

### 获取实例

```typescript
import { getWSClient } from "@/services/wsClient";

const client = getWSClient(); // 全局单例
```

### 连接

```typescript
// 开发环境（Vite 自动代理 /ws → localhost:8000/ws）
await client.connect(`ws://${window.location.host}/ws`);

// 生产环境（直接指定后端地址）
await client.connect("ws://your-server.com:8000/ws");
```

### 订阅频道数据

```typescript
import type { Chart4Payload } from "@/services/types";

// 订阅 chart4 频道
const unsubscribe = client.subscribe<Chart4Payload>("chart4", (payload) => {
  console.log("Chart4 更新:", payload.total_revenue);
});

// 不再需要时取消订阅
unsubscribe();
```

### 监听连接状态

```typescript
client.onStatusChange((status) => {
  console.log("连接状态:", status);
  // "connecting" | "connected" | "reconnecting" | "disconnected"
});

// 获取当前状态
const status = client.getStatus();
```

### 断开连接

```typescript
client.disconnect(); // 主动断开，不会自动重连
```

---

## 自动重连机制

```
第 1 次断开 → 等待 1 秒 → 重连
第 2 次断开 → 等待 2 秒 → 重连
第 3 次断开 → 等待 4 秒 → 重连
第 4 次断开 → 等待 8 秒 → 重连
...
最多等待 30 秒 → 之后每次断连等待 30 秒重连
```

> 🔧 指数退避（Exponential Backoff）：重连越来越慢，避免形成"重连风暴"。

---

## 如何新增数据频道

以新增 `chart1` 频道为例：

### 1. 后端新增频道

在 `server/src/` 中参照 `models/chart4.py` 和 `data/chart4_data.py` 的模式创建对应的模型和数据层。然后在 `tcp_server.py` 的 handler 中新增对 `chart1_update` 类型的处理。

### 2. 前端新增类型

在 `src/services/types.ts` 中新增 `Chart1Payload` 接口。

### 3. dataStore 新增订阅

在 `src/pages/DataCenter/stores/dataStore.ts` 的 `initialize` 方法中：
```typescript
_unsubscribeChart1 = client.subscribe<Chart1Payload>("chart1", (payload) => {
  set({ chart1: payload });
});
```
在 `reset` 方法中：
```typescript
_unsubscribeChart1?.();
```

### 4. 组件读取

在 `chart1.tsx` 中：
```typescript
const chart1Data = useDataStore((s) => s.chart1);
```
