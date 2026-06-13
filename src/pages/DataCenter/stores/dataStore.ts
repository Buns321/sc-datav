/**
 * dataStore.ts — 后端数据状态管理（Zustand）
 *
 * 这个 Store 管理后端数据的存储与初始加载。
 * WebSocket 连接由 demo.tsx 中的 useEffect 直接管理。
 *
 * 数据流:
 *   1. fetchInitialData()  — 页面加载时通过 HTTP GET 立即获取最新缓存
 *   2. WebSocket onmessage — 后续实时更新通过推送到达
 */

import { create } from "zustand";
import { DC } from "@/config/config";
import type { Chart4Payload, ConnectionStatus } from "@/services/types";

interface DataStore {
  /** Chart4（企业收益统计）的当前数据 */
  chart4: Chart4Payload | null;

  /** WebSocket 当前连接状态 */
  connectionStatus: ConnectionStatus;

  /** 设置 Chart4 数据（由 demo.tsx 的 WebSocket onmessage 调用） */
  setChart4: (data: Chart4Payload | null) => void;

  /** 设置连接状态 */
  setConnectionStatus: (status: ConnectionStatus) => void;

  /**
   * 从后端 HTTP API 拉取初始数据
   *
   * 在 WebSocket 连接建立前调用，确保页面刷新时首屏不空白。
   * 如果请求失败（后端未启动），静默降级——组件中已有 DEFAULT_DATA fallback。
   */
  fetchInitialData: () => Promise<void>;
}

export const useDataStore = create<DataStore>()((set) => ({
  chart4: null,
  connectionStatus: "disconnected",

  setChart4: (data) => set({ chart4: data }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),

  fetchInitialData: async () => {
    try {
      const res = await fetch(DC.api.chart4);
      if (!res.ok) {
        console.warn("[dataStore] GET /api/charts/4 返回非 200:", res.status);
        return;
      }
      const payload: Chart4Payload = await res.json();
      set({ chart4: payload });
      console.log("[dataStore] 初始数据已加载:", {
        total_revenue: payload.total_revenue,
        enterprise_count: payload.enterprise_count,
      });
    } catch (err) {
      // 后端未启动或网络不可达时静默降级
      console.warn("[dataStore] 无法获取初始数据，将使用默认值:", err);
    }
  },
}));
