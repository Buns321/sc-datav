/**
 * dataStore.ts — 后端数据状态管理（Zustand）
 *
 * 这个 Store 只管理后端数据的存储，不负责连接逻辑。
 * WebSocket 连接由 demo.tsx 中的 useEffect 直接管理。
 */

import { create } from "zustand";
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
}

export const useDataStore = create<DataStore>()((set) => ({
  chart4: null,
  connectionStatus: "disconnected",

  setChart4: (data) => set({ chart4: data }),
  setConnectionStatus: (status) => set({ connectionStatus: status }),
}));
