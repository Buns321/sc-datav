import { useEffect, useMemo, useRef } from "react";
import styled from "styled-components";
import { useConfigStore } from "./stores";
import { useDataStore } from "./stores/dataStore";
import { applyTokens, lightTokens, darkTokens, generateTokens } from "./theme";
import type { TokenMap } from "./theme";
import { DC } from "@/config/config";
import Panel from "./panel";
import Map from "./map";

const Wrapper = styled.div`
  position: relative;
  width: 100vw;
  height: 100vh;
`;

export default function Index() {
  const themeMode = useConfigStore((s) => s.themeMode);
  const seedColor = useConfigStore((s) => s.seedColor);

  // 保存 WebSocket 实例引用（组件级，避免 StrictMode 双 mount 误关连接）
  const wsRef = useRef<WebSocket | null>(null);

  // 根据种子色和主题模式计算当前令牌
  const activeTokens: TokenMap = useMemo(() => {
    if (seedColor) {
      const { light, dark } = generateTokens(seedColor);
      return themeMode === "dark" ? dark : light;
    }
    return themeMode === "dark" ? darkTokens : lightTokens;
  }, [seedColor, themeMode]);

  // 注入 CSS 变量
  useEffect(() => {
    applyTokens(activeTokens);
  }, [activeTokens]);

  /**
   * 数据初始化流程
   *
   * 1. fetchInitialData() — HTTP GET /api/charts/4
   *    页面刷新时立即拉取引擎中的最新缓存，首屏不空白。
   *    如果后端未启动或请求失败，静默降级（组件有 DEFAULT_DATA fallback）。
   *
   * 2. WebSocket 连接 — ws://.../ws
   *    建立后持续接收推送，覆盖 dataStore 中的数据。
   *
   * 用 useRef 保存 WebSocket 实例，避免 StrictMode 双 mount 误关连接。
   * 用 setTimeout(0) 延迟创建，确保 StrictMode cleanup 不会立即关掉新建的 socket。
   */
  useEffect(() => {
    // ① 先通过 HTTP 拉取初始数据（不等待，Fire-and-forget）
    useDataStore.getState().fetchInitialData();

    // ② 再建立 WebSocket 连接
    const setChart4 = useDataStore.getState().setChart4;
    const setConnectionStatus = useDataStore.getState().setConnectionStatus;

    const timer = setTimeout(() => {
      const ws = new WebSocket(DC.ws.url);
      wsRef.current = ws;

      ws.onopen = () => setConnectionStatus("connected");
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (DC.ws.channels.includes(msg.channel) && msg.payload) {
            if (msg.channel === "chart4") setChart4(msg.payload);
          }
        } catch { /* ignore parse errors */ }
      };
      ws.onclose = () => setConnectionStatus("disconnected");
      ws.onerror = () => setConnectionStatus("disconnected");
    }, 0);

    return () => {
      clearTimeout(timer);
      // 如果 WebSocket 已创建，关闭它
      if (wsRef.current) {
        wsRef.current.close();
      }
      setConnectionStatus("disconnected");
      setChart4(null);
    };
  }, []);

  useEffect(() => {
    return useConfigStore.getState().reset();
  }, []);

  return (
    <Wrapper>
      <Map />
      <Panel activeTokens={activeTokens} />
    </Wrapper>
  );
}
