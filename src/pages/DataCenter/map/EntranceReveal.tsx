import { useLayoutEffect, useRef, type ReactNode } from "react";
import { useThree } from "@react-three/fiber";
import { gsap } from "gsap";
import { type Group } from "three";
import { useConfigStore } from "../stores";
import {
  CAMERA_SWEEP,
  CAMERA_END,
  REVEAL_DURATION,
} from "./camera";

export interface EntranceRevealProps {
  children: ReactNode;
}

export default function EntranceReveal({ children }: EntranceRevealProps) {
  const groupRef = useRef<Group>(null!);
  const camera = useThree((s) => s.camera);

  useLayoutEffect(() => {
    if (!groupRef.current) return;

    const tl = gsap.timeline({
      onComplete: () => {
        useConfigStore.setState({ mapPlayComplete: true });
      },
    });

    // 第一段：相机绕到侧面（制造动态感）
    tl.to(camera.position, {
      ...CAMERA_SWEEP,
      duration: REVEAL_DURATION.sweep,
      ease: "circ.out",
    });

    // 最后一段：相机回到正面
    tl.to(camera.position, {
      x: CAMERA_END.x,
      y: CAMERA_END.y,
      z: CAMERA_END.z,
      duration: REVEAL_DURATION.home,
      ease: "power2.inOut",
    });

    return () => {
      tl.kill();
    };
  }, [camera]);

  return (
    <group ref={groupRef}>
      {children}
    </group>
  );
}
