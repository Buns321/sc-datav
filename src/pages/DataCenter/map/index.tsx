import styled from "styled-components";
import { useMemo } from "react";
import { Canvas } from "@react-three/fiber";
import { ContactShadows, OrbitControls } from "@react-three/drei";
import Lights from "./lights";
import Scene from "./scene";
import { CAMERA_INITIAL } from "./camera";
import { useConfigStore } from "../stores";
import { generateTokens, lightTokens, darkTokens } from "../theme";

const CanvasWrapper = styled.div`
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
`;

export default function Index() {
  const seedColor = useConfigStore((s) => s.seedColor);
  const themeMode = useConfigStore((s) => s.themeMode);

  const bgColor = useMemo(() => {
    if (seedColor) {
      const { light, dark } = generateTokens(seedColor);
      return (themeMode === "dark" ? dark : light).surface;
    }
    return (themeMode === "dark" ? darkTokens : lightTokens).surface;
  }, [seedColor, themeMode]);

  return (
    <CanvasWrapper>
      <Canvas
        flat
        shadows
        camera={{ position: [CAMERA_INITIAL.x, CAMERA_INITIAL.y, CAMERA_INITIAL.z], fov: 50, far: 2000, near: 1 }}
        dpr={[1, 2]}>
        <color attach="background" args={[bgColor]} />
        <Lights />

        <Scene />

        <ContactShadows
          opacity={0.5}
          scale={300}
          blur={0.5}
          resolution={256}
          color="#000000"
        />

        <OrbitControls
          enablePan
          enableZoom
          enableRotate
          zoomSpeed={0.3}
          minDistance={100}
          maxDistance={300}
          maxPolarAngle={1.5}
        />
      </Canvas>
    </CanvasWrapper>
  );
}
