// 相机坐标 & 动画参数常量 —— 类似 C 的 #define 区
// 改一处，全局生效

/** Canvas 初始相机位置 */
export const CAMERA_INITIAL = {
  x: -100,
  y: 0,
  z: 100,
} as const;

/** 入场动画第一段：相机绕到的侧面位置 */
export const CAMERA_SWEEP = {
  x: 0,
  y: 200,
  z: 50,
} as const;

/** 入场动画最后一段：相机回到的正面位置 */
export const CAMERA_END = {
  x: 0,
  y: 150,
  z: 150,
} as const;

/** 入场动画时长（秒） */
export const REVEAL_DURATION = {
  sweep: 3,       // 相机绕侧面
  home: 3,        // 相机回正面
  recenter: 5,    // 用户停止交互后，相机自动回正的冷却时间（秒）
} as const;
