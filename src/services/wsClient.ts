/**
 * wsClient.ts — WebSocket 客户端（单例）
 *
 * 封装了浏览器原生的 WebSocket API，提供：
 *   1. 自动重连（指数退避策略）
 *   2. 心跳检测（Ping/Pong）
 *   3. 频道订阅管理
 *   4. 连接状态暴露
 *
 * 🔧 写给嵌入式开发者 —— WebSocket 和 TCP 的关系：
 *
 * 浏览器中的 WebSocket 就是基于 TCP 的全双工通信协议。
 * 你可以把 WebSocket 理解为"加了标准化握手过程的 TCP 连接"。
 * 浏览器没有原始 TCP API，WebSocket 是浏览器能做的最底层网络通信。
 *
 * 本项目的完整链路：
 *   上位机 ──原始 TCP──→ Python 后端 ──WebSocket──→ 浏览器
 *
 * 这个 WSClient 负责最后一段——从后端到浏览器的 WebSocket 连接。
 */

import type { Chart4Message, ConnectionStatus } from "./types";

// ============================================================================
// 重连策略配置
// ============================================================================

/** 初始重连延迟（毫秒） */
const INITIAL_RECONNECT_DELAY = 1000;

/** 最大重连延迟（毫秒）—— 最多等 30 秒 */
const MAX_RECONNECT_DELAY = 30000;

/** 退避乘数 —— 每次重连失败后，延迟 ×2 */
const BACKOFF_MULTIPLIER = 2;

/** 心跳间隔（毫秒）—— 每 30 秒发一次 Ping */
const HEARTBEAT_INTERVAL = 30000;

// ============================================================================
// WSClient 类
// ============================================================================

/**
 * WebSocket 客户端单例
 *
 * 使用方式：
 *   const client = getWSClient();
 *   await client.connect("ws://localhost:8000/ws");
 *   const unsub = client.subscribe<Chart4Payload>("chart4", (data) => { ... });
 *
 *   页面卸载时：
 *   client.disconnect();  // 或在 useEffect 的 cleanup 中调用
 */
class WSClient {
  /** 原生 WebSocket 实例 */
  private _ws: WebSocket | null = null;

  /** 后端 URL */
  private _url: string = "";

  /** 当前连接状态 */
  private _status: ConnectionStatus = "disconnected";

  /** 状态变化回调列表 */
  private _statusCallbacks: Array<(status: ConnectionStatus) => void> = [];

  /** 频道订阅者映射：channel → callback[] */
  private _subscribers: Map<string, Array<(payload: unknown) => void>> =
    new Map();

  /** 重连计时器 ID */
  private _reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  /** 当前重连延迟 */
  private _reconnectDelay: number = INITIAL_RECONNECT_DELAY;

  /** 心跳计时器 ID */
  private _heartbeatTimer: ReturnType<typeof setInterval> | null = null;

  /** 是否由用户主动断开（主动断开时不自动重连） */
  private _manualDisconnect: boolean = false;

  // ========================================================================
  // 连接管理
  // ========================================================================

  /**
   * 建立 WebSocket 连接
   *
   * @param url - 后端 WebSocket 地址，如 "ws://localhost:8000/ws"
   *              开发环境下可以省略协议和域名，由 Vite proxy 处理
   *
   * 🔧 开发环境下的地址说明：
   * 因为 Vite 配置了 proxy: { "/ws": { target: "ws://localhost:8000", ws: true } }
   * 所以前端可以写 `ws://${location.host}/ws` 或直接用相对路径构建 URL。
   */
  async connect(url: string): Promise<void> {
    // 如果已经连接了，先断开
    if (this._ws) {
      this._cleanup();
    }

    this._url = url;
    this._manualDisconnect = false;

    return new Promise((resolve, reject) => {
      try {
        this._setStatus("connecting");
        this._ws = new WebSocket(url);

        // 连接成功时的回调
        this._ws.onopen = () => {
          this._setStatus("connected");
          this._reconnectDelay = INITIAL_RECONNECT_DELAY; // 重连成功后重置延迟
          this._startHeartbeat(); // 开始心跳
          resolve();
        };

        // 收到消息时的回调
        this._ws.onmessage = (event: MessageEvent) => {
          this._handleMessage(event.data);
        };

        // 连接关闭时的回调（可能是主动关闭，也可能是网络断开）
        this._ws.onclose = () => {
          this._stopHeartbeat();
          this._attemptReconnect();
        };

        // 连接出错时的回调
        this._ws.onerror = (error: Event) => {
          // 如果还没连接成功，reject Promise
          if (this._status === "connecting") {
            reject(new Error("WebSocket 连接失败"));
          }
          console.error("[WSClient] WebSocket 错误:", error);
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * 主动断开 WebSocket 连接
   *
   * 调用此方法后不会自动重连。
   * 页面卸载时应该调用此方法，避免后台一直尝试重连消耗资源。
   */
  disconnect(): void {
    this._manualDisconnect = true;
    this._cleanup();
    this._setStatus("disconnected");
  }

  // ========================================================================
  // 频道订阅
  // ========================================================================

  /**
   * 订阅一个数据频道
   *
   * 当后端通过 WebSocket 推送数据时，会根据 channel 字段
   * 将 payload 分发给对应的订阅者回调。
   *
   * @param channel  - 频道名称，如 "chart4"
   * @param callback - 收到数据时调用的回调函数
   * @returns 取消订阅的函数（类似 useEffect 的 cleanup 返回值）
   *
   * 使用示例：
   *   const unsubscribe = client.subscribe<Chart4Payload>("chart4", (data) => {
   *     console.log("Chart4 数据更新:", data.total_revenue);
   *   });
   *   // 不再需要时
   *   unsubscribe();
   */
  subscribe<T>(channel: string, callback: (payload: T) => void): () => void {
    // 如果这个频道还没有订阅者列表，创建一个
    if (!this._subscribers.has(channel)) {
      this._subscribers.set(channel, []);
    }

    // 添加回调到订阅者列表
    const callbacks = this._subscribers.get(channel)!;
    callbacks.push(callback as (payload: unknown) => void);

    // 返回取消订阅的函数
    // 🔧 这是一个"闭包"（Closure）：返回值捕获了 channel 和 callback
    // 类比：React 中 useEffect 返回的 cleanup 函数
    return () => {
      const cbs = this._subscribers.get(channel);
      if (cbs) {
        const idx = cbs.indexOf(callback as (payload: unknown) => void);
        if (idx !== -1) {
          cbs.splice(idx, 1);
        }
      }
    };
  }

  // ========================================================================
  // 连接状态
  // ========================================================================

  /**
   * 获取当前连接状态
   */
  getStatus(): ConnectionStatus {
    return this._status;
  }

  /**
   * 注册连接状态变化监听
   *
   * @param callback - 状态变化时的回调
   * @returns 取消监听的函数
   */
  onStatusChange(callback: (status: ConnectionStatus) => void): () => void {
    this._statusCallbacks.push(callback);
    // 立即通知当前状态
    callback(this._status);
    return () => {
      const idx = this._statusCallbacks.indexOf(callback);
      if (idx !== -1) {
        this._statusCallbacks.splice(idx, 1);
      }
    };
  }

  // ========================================================================
  // 内部方法
  // ========================================================================

  /**
   * 更新连接状态并通知所有监听者
   */
  private _setStatus(status: ConnectionStatus): void {
    this._status = status;
    // 通知所有注册的状态回调
    for (const cb of this._statusCallbacks) {
      cb(status);
    }
  }

  /**
   * 处理收到的 WebSocket 消息
   *
   * 🔧 消息格式（与后端约定）：
   * {
   *   "type": "data",
   *   "channel": "chart4",
   *   "payload": { ... 实际数据 ... },
   *   "timestamp": "2026-05-28T12:00:00Z"
   * }
   */
  private _handleMessage(rawData: string): void {
    try {
      // 步骤 1：解析 JSON 字符串 → JavaScript 对象
      const message: Chart4Message = JSON.parse(rawData);

      // 步骤 2：根据 channel 字段，找到对应的订阅者
      const channel = message.channel;
      const callbacks = this._subscribers.get(channel);

      if (callbacks && callbacks.length > 0) {
        // 步骤 3：依次调用所有订阅者回调，传递 payload
        for (const cb of callbacks) {
          try {
            // 🔧 try/catch 包裹每个回调：一个回调报错不影响其他回调
            cb(message.payload);
          } catch (error) {
            console.error(
              `[WSClient] 频道 "${channel}" 的回调执行出错:`,
              error
            );
          }
        }
      }
    } catch (error) {
      console.error("[WSClient] 消息解析失败:", error);
    }
  }

  /**
   * 尝试自动重连（指数退避策略）
   *
   * 🔧 指数退避（Exponential Backoff）：
   *   第 1 次重连等 1 秒 → 第 2 次等 2 秒 → 第 3 次等 4 秒 → ...
   *   最多等 30 秒。
   *
   * 为什么需要退避？
   *   如果后端因为负载过高而断开，所有前端同时立即重连
   *   会形成"重连风暴"，加重后端负担。退避让重连请求分散开。
   */
  private _attemptReconnect(): void {
    // 如果是用户主动断开，不重连
    if (this._manualDisconnect) {
      this._setStatus("disconnected");
      return;
    }

    this._setStatus("reconnecting");

    // 清除之前的重连计时器（如果存在）
    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
    }

    // 设置下一次重连
    console.log(
      `[WSClient] ${this._reconnectDelay / 1000} 秒后尝试重连...`
    );

    this._reconnectTimer = setTimeout(() => {
      console.log("[WSClient] 正在重连...");

      // 🔧 connect() 方法返回 Promise，但这里不需要 await
      // 如果重连成功，onopen 回调会重置状态和延迟
      // 如果重连失败，onclose 会再次触发 _attemptReconnect
      this.connect(this._url).catch(() => {
        // 重连失败，增加延迟（指数退避）
        this._reconnectDelay = Math.min(
          this._reconnectDelay * BACKOFF_MULTIPLIER,
          MAX_RECONNECT_DELAY
        );
      });
    }, this._reconnectDelay);
  }

  /**
   * 开始心跳检测
   *
   * 🔧 心跳（Heartbeat/Ping-Pong）：
   *   定期发送一个很小的消息（Ping），如果对方回应（Pong），
   *   说明连接正常。如果连续几次没有 Pong，说明连接可能已经"假死"。
   *
   * 为什么需要心跳？
   *   TCP 的连接断开有时不会被立即检测到（比如网线拔了但不发数据）。
   *   心跳就是一个"你还在吗？"的定期检查。
   *
   * 注意：浏览器 WebSocket 的 Ping/Pong 由浏览器自动处理（RFC 6455），
   * 应用层一般不需要手动实现。但为了清晰展示原理，这里保留实现框架。
   */
  private _startHeartbeat(): void {
    this._stopHeartbeat(); // 先清除旧的
    this._heartbeatTimer = setInterval(() => {
      if (this._ws && this._ws.readyState === WebSocket.OPEN) {
        // 发送一个空消息作为心跳（有些后端会回复 Pong）
        // 如果后端不做区分，这也是无害的
        this._ws.send(JSON.stringify({ type: "ping" }));
      }
    }, HEARTBEAT_INTERVAL);
  }

  /**
   * 停止心跳检测
   */
  private _stopHeartbeat(): void {
    if (this._heartbeatTimer) {
      clearInterval(this._heartbeatTimer);
      this._heartbeatTimer = null;
    }
  }

  /**
   * 清理所有资源
   */
  private _cleanup(): void {
    this._stopHeartbeat();

    if (this._reconnectTimer) {
      clearTimeout(this._reconnectTimer);
      this._reconnectTimer = null;
    }

    if (this._ws) {
      // 🔧 onclose 中会再次触发 _attemptReconnect，
      // 清理时先移除 onclose 避免重连
      this._ws.onclose = null;
      this._ws.close();
      this._ws = null;
    }
  }
}

// ============================================================================
// 全局单例
//
// 🔧 为什么用单例？
// 整个应用只需要一条 WebSocket 连接。单例确保不会意外创建多条连接。
// 类比：一个浏览器标签页只需要连接一次服务器。
// ============================================================================

let _instance: WSClient | null = null;

/**
 * 获取 WSClient 单例
 */
export function getWSClient(): WSClient {
  if (!_instance) {
    _instance = new WSClient();
  }
  return _instance;
}
