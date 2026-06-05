import { useLayoutEffect, useRef, type ReactNode } from "react";
import { useThree } from "@react-three/fiber";
import { gsap } from "gsap";
import { type Group } from "three";
import { useConfigStore } from "../stores";
import { DC } from "@/config/config";

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
      ...DC.camera.sweep,
      duration: DC.camera.revealDuration.sweep,
      ease: "circ.out",
    });

    // 最后一段：相机回到正面
    tl.to(camera.position, {
      x: DC.camera.end.x,
      y: DC.camera.end.y,
      z: DC.camera.end.z,
      duration: DC.camera.revealDuration.home,
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
