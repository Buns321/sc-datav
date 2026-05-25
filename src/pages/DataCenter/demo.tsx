import { useEffect, useMemo } from "react";
import styled from "styled-components";
import { useConfigStore } from "./stores";
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
