import { useMemo, useRef } from "react";
import { DirectionalLight } from "three";
import { useConfigStore } from "../stores";
import { generateTokens, lightTokens, darkTokens } from "../theme";
import { DC } from "@/config/config";

export default function Lights() {
  const lightRef = useRef<DirectionalLight>(null!);
  const seedColor = useConfigStore((s) => s.seedColor);
  const themeMode = useConfigStore((s) => s.themeMode);

  const surfaceColor = useMemo(() => {
    if (seedColor) {
      const { light, dark } = generateTokens(seedColor);
      return (themeMode === "dark" ? dark : light).surface;
    }
    return (themeMode === "dark" ? darkTokens : lightTokens).surface;
  }, [seedColor, themeMode]);

  return (
    <>
      <ambientLight intensity={DC.lights.ambient.intensity} />
      <directionalLight
        ref={lightRef}
        intensity={DC.lights.directional.intensity}
        position={[...DC.lights.directional.position]}
        color={surfaceColor}
      />
    </>
  );
}
