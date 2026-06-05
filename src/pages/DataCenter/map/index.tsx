import styled from "styled-components";
import { useMemo, useRef } from "react";
import { Canvas } from "@react-three/fiber";
import { ContactShadows, OrbitControls } from "@react-three/drei";
import Lights from "./lights";
import Scene from "./scene";
import CameraAutoRecenter from "./CameraAutoRecenter";
import { DC } from "@/config/config";
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

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const controlsRef = useRef<any>(null);

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
        camera={{ position: [DC.camera.initial.x, DC.camera.initial.y, DC.camera.initial.z], fov: DC.camera.fov, far: DC.camera.far, near: DC.camera.near }}
        dpr={[...DC.camera.dpr]}>
        <color attach="background" args={[bgColor]} />
        <Lights />

        <Scene />

        <CameraAutoRecenter controlsRef={controlsRef} />

        <ContactShadows
          opacity={DC.effects.contactShadows.opacity}
          scale={DC.effects.contactShadows.scale}
          blur={DC.effects.contactShadows.blur}
          resolution={DC.effects.contactShadows.resolution}
          color={DC.effects.contactShadows.color}
        />

        <OrbitControls
          ref={controlsRef}
          enablePan={DC.controls.enablePan}
          enableZoom={DC.controls.enableZoom}
          enableRotate={DC.controls.enableRotate}
          zoomSpeed={DC.controls.zoomSpeed}
          minDistance={DC.controls.minDistance}
          maxDistance={DC.controls.maxDistance}
          maxPolarAngle={DC.controls.maxPolarAngle}
        />
      </Canvas>
    </CanvasWrapper>
  );
}
