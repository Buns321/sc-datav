import { useEffect, useMemo, useRef } from "react";
import styled from "styled-components";
import { useConfigStore } from "./stores";
import { useDataStore } from "./stores/dataStore";
import { applyTokens, lightTokens, darkTokens, generateTokens } from "./theme";
import type { TokenMap } from "./theme";
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
   * ⚡ WebSocket 直接连接
   *
   * 用 useRef 保存 WebSocket 实例，避免 StrictMode 双 mount 误关连接。
   * 用 setTimeout(0) 延迟创建，确保 StrictMode cleanup 不会立即关掉新建的 socket。
   */
  useEffect(() => {
    const wsRef = { current: null as WebSocket | null };
    const setChart4 = useDataStore.getState().setChart4;
    const setConnectionStatus = useDataStore.getState().setConnectionStatus;

    const timer = setTimeout(() => {
      const ws = new WebSocket("ws://localhost:8000/ws");
      wsRef.current = ws;

      ws.onopen = () => setConnectionStatus("connected");
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.channel === "chart4" && msg.payload) {
            setChart4(msg.payload);
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
