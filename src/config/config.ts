/**
 * config.ts — DataCenter 大屏统一配置
 *
 * 这是整个 DataCenter 场景的"控制面板"。修改这里的值 =
 * 修改摄像机、3D 材质、灯光、面板文案、特性开关——全部行为。
 *
 * 使用方式：
 *   import { DC, CHART_TEXTS } from "@/config/config";
 *   组件中通过 DC.camera.initial、CHART_TEXTS.chart4.title 等引用
 *
 * 架构约束：
 *   - 所有常量集中在此文件，组件禁止硬编码 magic number
 *   - 运行时状态（如用户切换主题）仍存储在 Zustand configStore
 *   - 主题色系统（tokens/palette）保持独立，这里仅存默认种子色
 */

// ══════════════════════════════════════════════════════════════════════════
// 1. 3D 摄像机
// ══════════════════════════════════════════════════════════════════════════

const camera = {
  /** Canvas 初始相机位置 */
  initial: { x: -100, y: 0, z: 100 },
  /** 入场动画第一段：相机绕到的侧面位置 */
  sweep: { x: 0, y: 200, z: 50 },
  /** 入场动画最后一段：相机回到的正面位置 */
  end: { x: 0, y: 150, z: 150 },

  /** Canvas 相机参数 */
  fov: 50,
  far: 2000,
  near: 1,
  dpr: [1, 2] as readonly [number, number],

  /** 入场动画时长（秒） */
  revealDuration: {
    sweep: 3,
    home: 3,
    /** 用户停止交互后，相机自动回正的冷却时间（秒） */
    recenter: 5,
  },
} as const;

// ══════════════════════════════════════════════════════════════════════════
// 2. 3D 灯光
// ══════════════════════════════════════════════════════════════════════════

const lights = {
  ambient: { intensity: 2 },
  directional: { intensity: 12, position: [0, 200, 20] as readonly [number, number, number] },
} as const;

// ══════════════════════════════════════════════════════════════════════════
// 3. 3D 材质 — 机房模型 (server_room.glb)
// ══════════════════════════════════════════════════════════════════════════

const materials = {
  body:       { color: "#1e2d3d", roughness: 0.6, metalness: 0.3 },
  rack:       { color: "#2c3e50", roughness: 0.6, metalness: 0.3 },
  floor:      { color: "#ffffff", roughness: 0.8, metalness: 0.1 },
  camera:     { color: "#444444", roughness: 0.4, metalness: 0.6 },
  swBox:      { color: "#3d5a80", roughness: 0.5, metalness: 0.5 },
  sw:         { color: "#4a6fa5", roughness: 0.3, metalness: 0.7 },
  fireKiller: { color: "#c0392b", roughness: 0.3, metalness: 0.5 },
  default:    { color: "#888888", roughness: 0.6, metalness: 0.3 },
} as const;

// ══════════════════════════════════════════════════════════════════════════
// 4. 视觉效果
// ══════════════════════════════════════════════════════════════════════════

const effects = {
  contactShadows: {
    opacity: 0.5,
    scale: 300,
    blur: 0.5,
    resolution: 256,
    color: "#000000",
  },
} as const;

// ══════════════════════════════════════════════════════════════════════════
// 5. 轨道控制器 (OrbitControls)
// ══════════════════════════════════════════════════════════════════════════

const controls = {
  enablePan: true,
  enableZoom: true,
  enableRotate: true,
  zoomSpeed: 0.3,
  minDistance: 100,
  maxDistance: 300,
  maxPolarAngle: 1.5,
} as const;

// ══════════════════════════════════════════════════════════════════════════
// 6. 特性开关默认值（运行时可通过 configStore 切换）
// ══════════════════════════════════════════════════════════════════════════

const features = {
  cloud: true,
  bar: true,
  rotation: true,
  heat: true,
  mode: true,
  themeMode: "light" as "light" | "dark",
  seedColor: undefined as string | undefined,
} as const;

// ══════════════════════════════════════════════════════════════════════════
// 7. 文案 — 所有面向用户的文字
// ══════════════════════════════════════════════════════════════════════════

interface ChartCardTexts {
  title: string;
  subtitle: string;
}

export const CHART_TEXTS = {
  chart1: {
    title: "2025年规模指标分析",
    subtitle: "INDICATOR ANALYSIS",
  } satisfies ChartCardTexts,

  chart2: {
    title: "企业税收分析",
    subtitle: "TAX ANALYSIS",
  } satisfies ChartCardTexts,

  chart3: {
    title: "行政处罚信息",
    subtitle: "PENALTY INFORMATION",
  } satisfies ChartCardTexts,

  chart4: {
    title: "企业收益总数统计",
    subtitle: "REVENUE STATISTICS",
    revenueLabel: "收益总计",
    revenueUnit: "亿万元",
    enterpriseLabel: "企业数量",
  } satisfies ChartCardTexts & {
    revenueLabel: string;
    revenueUnit: string;
    enterpriseLabel: string;
  },

  chart5: {
    title: "企业能耗分析",
    subtitle: "ENERGY CONSUMPTION ANALYSIS",
  } satisfies ChartCardTexts,

  chart6: {
    title: "企业税收分析",
    subtitle: "TAX ANALYSIS",
  } satisfies ChartCardTexts,

  header: {
    title: "四川省智慧城市数据大脑",
    subtitle: "SICHUAN SMART BRAIN",
  },
} as const;

// ══════════════════════════════════════════════════════════════════════════
// 统一导出
// ══════════════════════════════════════════════════════════════════════════

export const DC = {
  camera,
  lights,
  materials,
  effects,
  controls,
  features,
} as const;

export type DCConfig = typeof DC;
