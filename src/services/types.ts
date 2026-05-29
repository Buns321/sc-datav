/**
 * types.ts — 前后端共享的数据类型定义
 *
 * 这个文件定义的数据结构必须与后端 server/src/models/chart4.py 保持一致。
 * 如果改了后端的数据格式，一定要同步修改这个文件。
 *
 * 这叫做"契约"（Contract）——前后端约定的数据格式。
 * 类比：REST API 的 OpenAPI/Swagger 文档，这里用 TypeScript 类型来表达。
 */

/**
 * Chart4（企业收益统计）的业务数据
 *
 * 对应后端 Chart4Payload Pydantic 模型
 */
export interface Chart4Payload {
  /** 折线图的 10 个数据点（对应图表的 Y 轴值） */
  line_data: number[];

  /** 收益总计，单位：亿元 */
  total_revenue: number;

  /** 企业总数，单位：个 */
  enterprise_count: number;
}

/**
 * Chart4 的完整消息格式
 *
 * 这是 WebSocket 推送的 JSON 消息结构。
 * 对应后端 Chart4Message Pydantic 模型。
 */
export interface Chart4Message {
  /** 消息类型，固定为 "data" */
  type: "data";

  /** 数据频道，固定为 "chart4" */
  channel: "chart4";

  /** Chart4 的实际业务数据 */
  payload: Chart4Payload;

  /** 报文发送时间 */
  timestamp: string;
}

/**
 * WebSocket 连接状态枚举
 *
 * 类似前端的 RTCPeerConnection 状态机：
 * connecting → connected → (reconnecting → connected) → disconnected
 */
export type ConnectionStatus =
  | "connecting"    // 正在建立连接
  | "connected"     // 已连接，可以通信
  | "reconnecting"  // 连接断开，正在尝试重连（指数退避）
  | "disconnected"; // 已断开，不会自动重连（手动 disconnect 或重连次数超限）
