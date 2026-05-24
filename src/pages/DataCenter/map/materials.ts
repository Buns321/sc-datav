// 机房模型全局材质常量 —— 类似 C 的 #define 区
// 改一处，全局生效

export const COLORS = {
  body:       "#1e2d3d",   // 机柜柜体
  rack:       "#2c3e50",   // 机柜单元
  floor:      "#ffffff",   // 地板
  camera:     "#444444",   // 摄像头
  swBox:      "#3d5a80",   // 交换机盒
  sw:         "#4a6fa5",   // 交换机面板
  fireKiller: "#c0392b",   // 灭火器
  default:    "#888888",   // 未匹配的物体
} as const;

export const ROUGHNESS = {
  body:       0.6,
  rack:       0.6,
  floor:      0.8,
  camera:     0.4,
  swBox:      0.5,
  sw:         0.3,
  fireKiller: 0.3,
  default:    0.6,
} as const;

export const METALNESS = {
  body:       0.3,
  rack:       0.3,
  floor:      0.1,
  camera:     0.6,
  swBox:      0.5,
  sw:         0.7,
  fireKiller: 0.5,
  default:    0.3,
} as const;
