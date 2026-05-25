import { use, useEffect, useMemo, useRef } from "react";
import { useFrame, type ThreeElements } from "@react-three/fiber";
import {
  AdditiveBlending,
  Color,
  DoubleSide,
  InstancedMesh,
  Object3D,
  RepeatWrapping,
  SRGBColorSpace,
  type Mesh,
} from "three";
import { useConfigStore } from "../stores";
import { generateTokens, lightTokens, darkTokens } from "../theme";
import loadTexture from "../helpers/loadTexture";

import guangquan01 from "@/assets/guangquan01.png";
import huiguang from "@/assets/huiguang.png";

export interface CityBarProps {
  position?: ThreeElements["group"]["position"];
  value?: number;
  uColor1?: Color;
  uColor2?: Color;
  dir?: "x" | "y" | "z";
  factor?: number;
  max?: number;
  children?: React.ReactNode | ((barHeight: number) => React.ReactNode);
}
const textures = Promise.all([
  loadTexture(guangquan01),
  loadTexture(huiguang, (tex) => {
    tex.colorSpace = SRGBColorSpace;
    tex.wrapS = tex.wrapT = RepeatWrapping;
  }),
]);

export default function Bar(props: CityBarProps) {
  const {
    position,
    value = Math.floor(Math.random() * 1000) + 100,
    children,
    uColor1: _uColor1,
    uColor2: _uColor2,
    dir = "y",
    factor = 5,
    max = 1000,
  } = props;

  // 动态默认色：当调用方未传入 uColor1/uColor2 时，从当前主题取
  const seedColor = useConfigStore((s) => s.seedColor);
  const themeMode = useConfigStore((s) => s.themeMode);
  const defaultColor1 = useMemo(() => {
    if (seedColor) {
      const { light, dark } = generateTokens(seedColor);
      return new Color((themeMode === "dark" ? dark : light).secondary);
    }
    return new Color((themeMode === "dark" ? darkTokens : lightTokens).secondary);
  }, [seedColor, themeMode]);
  const defaultColor2 = useMemo(() => {
    if (seedColor) {
      const { light, dark } = generateTokens(seedColor);
      return new Color((themeMode === "dark" ? dark : light).primary);
    }
    return new Color((themeMode === "dark" ? darkTokens : lightTokens).primary);
  }, [seedColor, themeMode]);

  const uColor1 = _uColor1 ?? defaultColor1;
  const uColor2 = _uColor2 ?? defaultColor2;
  let dirMap = { x: 1.0, y: 2.0, z: 3.0 };

  const quanRef = useRef<Mesh>(null!);
  const bar = useConfigStore((s) => s.bar);

  const [texture1, texture2] = use(textures);

  const barHeight = useMemo(() => {
    return 4.0 * factor * (value / max);
  }, []);

  useFrame((_, delta) => {
    quanRef.current.rotation.z += delta + 0.02;
  });

  const meshRef = useRef<InstancedMesh>(null!);

  useEffect(() => {
    const rotations = [0, 60, 120];
    const object3D = new Object3D();

    rotations.forEach((deg, i) => {
      object3D.rotation.set(Math.PI / 2, (Math.PI / 180) * deg, 0);
      object3D.updateMatrix();
      meshRef.current.setMatrixAt(i, object3D.matrix);
    });

    meshRef.current.instanceMatrix.needsUpdate = true;
  }, []);

  return (
    <group visible={bar} position={position}>
      <mesh
        renderOrder={5}
        position={[0, 0, barHeight / 2]}
        raycast={() => null}>
        <instancedMesh
          ref={meshRef}
          matrixAutoUpdate={false}
          args={[undefined, undefined, 3]}
          renderOrder={10}
          rotation-x={Math.PI / 2}
          raycast={() => null}>
          <planeGeometry args={[3.5, barHeight]} />
          <meshBasicMaterial
            transparent
            color={uColor2}
            map={texture2}
            opacity={0.4}
            depthWrite={false}
            side={DoubleSide}
            blending={AdditiveBlending}
          />
        </instancedMesh>
        <boxGeometry
          args={[0.1 * factor, 0.1 * factor, barHeight]}
          translate={[0, 0, barHeight / 2]}
        />
        <meshBasicMaterial
          transparent
          color="#ffffff"
          opacity={1}
          depthTest={false}
          fog={false}
          onBeforeCompile={(shader) => {
            shader.uniforms = {
              ...shader.uniforms,
              uColor1: { value: uColor1 },
              uColor2: { value: uColor2 },
              uDir: { value: dirMap[dir] },
              uSize: { value: barHeight },
            };

            shader.vertexShader = shader.vertexShader.replace(
              "void main() {",
              `
                attribute float alpha;
                varying vec3 vPosition;
                varying float vAlpha;
                void main() {
                  vAlpha = alpha;
                  vPosition = position;
              `
            );
            shader.fragmentShader = shader.fragmentShader.replace(
              "void main() {",
              `
                varying vec3 vPosition;
                varying float vAlpha;
                uniform vec3 uColor1;
                uniform vec3 uColor2;
                uniform float uDir;
                uniform float uSize;

                void main() {
              `
            );
            shader.fragmentShader = shader.fragmentShader.replace(
              "#include <opaque_fragment>",
              /* glsl */ `
              #ifdef OPAQUE
              diffuseColor.a = 1.0;
              #endif

              // https://github.com/mrdoob/three.js/pull/22425
              #ifdef USE_TRANSMISSION
              diffuseColor.a *= transmissionAlpha + 0.1;
              #endif
              // vec3 gradient = mix(uColor1, uColor2, vPosition.x / 15.0);
              vec3 gradient = vec3(0.0,0.0,0.0);
              if(uDir==1.0){
                gradient = mix(uColor1, uColor2, vPosition.x/ uSize);
              }else if(uDir==2.0){
                gradient = mix(uColor1, uColor2, vPosition.z/ uSize);
              }else if(uDir==3.0){
                gradient = mix(uColor1, uColor2, vPosition.y/ uSize);
              }
              outgoingLight = outgoingLight * gradient;

              gl_FragColor = vec4( outgoingLight, diffuseColor.a  );
              `
            );
          }}
        />
      </mesh>
      <mesh renderOrder={6} ref={quanRef} raycast={() => null}>
        <planeGeometry args={[5, 5]} />
        <meshBasicMaterial
          transparent
          color={0xffffff}
          map={texture1}
          alphaMap={texture1}
          opacity={1}
          depthTest={false}
          fog={false}
          blending={AdditiveBlending}
        />
      </mesh>
      {typeof children === "function" ? children?.(barHeight) : children}
    </group>
  );
}
