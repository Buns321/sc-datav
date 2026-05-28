import { useEffect, useRef, type MutableRefObject } from "react";
import { useThree } from "@react-three/fiber";
import { gsap } from "gsap";
import { CAMERA_END, REVEAL_DURATION } from "./camera";
import { useConfigStore } from "../stores";

/** OrbitControls 默认的注视目标（场景原点附近） */
const DEFAULT_TARGET = { x: 0, y: 30, z: 0 } as const;

interface CameraAutoRecenterProps {
  /** OrbitControls 实例的 ref，由外层 Index 组件传入 */
  controlsRef: MutableRefObject<any>;
}

/**
 * 相机超时回正组件
 *
 * 放在 Canvas 内部（才能使用 useThree）。
 * 用户停止交互 REVEAL_DURATION.recenter 秒后，相机自动回到默认视角。
 * 仅在入场动画完成（mapPlayComplete）后才激活。
 */
export default function CameraAutoRecenter({ controlsRef }: CameraAutoRecenterProps) {
  const camera = useThree((s) => s.camera);
  const mapPlayComplete = useConfigStore((s) => s.mapPlayComplete);
  const recenterTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const recenterTweenRef = useRef<gsap.core.Tween | null>(null);

  useEffect(() => {
    if (!mapPlayComplete) return;
    const controls = controlsRef.current;
    if (!controls) return;

    const clearTimer = () => {
      if (recenterTimerRef.current !== null) {
        clearTimeout(recenterTimerRef.current);
        recenterTimerRef.current = null;
      }
    };

    const killTween = () => {
      if (recenterTweenRef.current) {
        recenterTweenRef.current.kill();
        recenterTweenRef.current = null;
      }
    };

    const onInteractionStart = () => {
      clearTimer();
      killTween();
    };

    const onInteractionEnd = () => {
      clearTimer();
      killTween();
      recenterTimerRef.current = setTimeout(() => {
        const from = {
          camX: camera.position.x,
          camY: camera.position.y,
          camZ: camera.position.z,
          targetX: controls.target.x,
          targetY: controls.target.y,
          targetZ: controls.target.z,
        };

        killTween();
        recenterTweenRef.current = gsap.to(from, {
          camX: CAMERA_END.x,
          camY: CAMERA_END.y,
          camZ: CAMERA_END.z,
          targetX: DEFAULT_TARGET.x,
          targetY: DEFAULT_TARGET.y,
          targetZ: DEFAULT_TARGET.z,
          duration: 1.5,
          ease: "power2.inOut",
          onUpdate: () => {
            camera.position.set(from.camX, from.camY, from.camZ);
            controls.target.set(from.targetX, from.targetY, from.targetZ);
            controls.update();
          },
        });
      }, REVEAL_DURATION.recenter * 1000);
    };

    controls.addEventListener("start", onInteractionStart);
    controls.addEventListener("end", onInteractionEnd);

    return () => {
      controls.removeEventListener("start", onInteractionStart);
      controls.removeEventListener("end", onInteractionEnd);
      clearTimer();
      killTween();
    };
  }, [mapPlayComplete, camera, controlsRef]);

  return null;
}
