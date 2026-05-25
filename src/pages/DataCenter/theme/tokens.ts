/**
 * 语义令牌映射 —— Monet 风格
 *
 * 将 RawTokens (Material Scheme hex) 映射为面向 UI 组件的语义令牌。
 * 组件引用令牌名，不引用具体色值 → 换种子色后零代码改动。
 */

import { generateSchemes, DEFAULT_SEED, type RawTokens } from "./palette";

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

/** 面向组件的完整令牌映射（亮色 / 暗色各一份） */
export interface TokenMap {
  // ---- Surface ----
  surface: string;
  surfaceContainer: string;
  surfaceOverlay: string;
  /** 卡片毛玻璃背景（亮色→白玻璃 rgba(255,255,255,0.7)，暗色→黑玻璃 rgba(15,15,18,0.55)） */
  cardGlassBg: string;

  // ---- Primary ----
  primary: string;
  primaryHover: string;
  primaryActive: string;
  primaryContainer: string;
  primaryGlow: string;
  onPrimary: string;

  // ---- Secondary ----
  secondary: string;
  secondaryVariant: string;
  secondaryContainer: string;
  secondaryDim: string;

  // ---- Accent ----
  accent: string;
  accentDim: string;

  // ---- Outline ----
  outline: string;
  outlineVariant: string;

  // ---- Text ----
  textPrimary: string;
  textSecondary: string;
  textTertiary: string;
  textDisabled: string;
  textHeading: string;
  textSubtitle: string;

  // ---- Shadow ----
  shadow: string;
  shadowStrong: string;

  // ---- Button ----
  buttonBg: string;
  buttonText: string;
  buttonBorder: string;
  buttonHoverBorder: string;
  buttonHoverText: string;
  buttonHoverShadow: string;
  buttonActiveBgStart: string;
  buttonActiveBgEnd: string;
  buttonActiveShadow: string;

  // ---- Header ----
  headerGradientStart: string;
  headerGradientEnd: string;
  headerTitleShadow: string;

  // ---- Footer ----
  footerGradientBg: string;

  // ---- Chart (仅 JS 使用) ----
  chartGradient: readonly [string, string];
  chartSeries: readonly [string, string, string, string];
  chartStatusGood: string;
  chartStatusWarn: string;
  chartStatusBad: string;

  // ---- Loading ----
  loadingWave: string;
}

// ---------------------------------------------------------------------------
// HSL 工具（用于生成辉光 / 阴影等 CSS 无法直接从 hex 推导的颜色）
// ---------------------------------------------------------------------------

/** hex → { h, s, l } (0-360, 0-100, 0-100) */
function hexToHsl(hex: string): { h: number; s: number; l: number } {
  let r = 0, g = 0, b = 0;
  const v = hex.replace("#", "");
  if (v.length === 3) {
    r = parseInt(v[0] + v[0], 16);
    g = parseInt(v[1] + v[1], 16);
    b = parseInt(v[2] + v[2], 16);
  } else {
    r = parseInt(v.substring(0, 2), 16);
    g = parseInt(v.substring(2, 4), 16);
    b = parseInt(v.substring(4, 6), 16);
  }
  r /= 255; g /= 255; b /= 255;
  const max = Math.max(r, g, b), min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;
  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return { h: Math.round(h * 360), s: Math.round(s * 100), l: Math.round(l * 100) };
}

/** hsl → hex */
function hslToHex(h: number, s: number, l: number): string {
  s /= 100; l /= 100;
  const a = s * Math.min(l, 1 - l);
  const f = (n: number) => {
    const k = (n + h / 30) % 12;
    const c = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
    return Math.round(255 * c).toString(16).padStart(2, "0");
  };
  return `#${f(0)}${f(8)}${f(4)}`;
}

// ---------------------------------------------------------------------------
// 令牌构建
// ---------------------------------------------------------------------------

/**
 * 从 RawTokens 构建面向组件的 TokenMap
 *
 * 大部分令牌直接映射 Material Scheme 的语义角色；
 * 辉光 / 阴影 / 按钮渐变等通过 primary 色相动态推算。
 */
export function createTokenMap(raw: RawTokens): TokenMap {
  const hsl = hexToHsl(raw.primary);

  // 动态推算 primary 色系变体（保证跨种子色一致可用）
  const primaryHover = hslToHex(hsl.h, Math.min(hsl.s + 10, 95), Math.min(hsl.l + 8, 95));
  const primaryActive = hslToHex(hsl.h, hsl.s, Math.max(hsl.l - 5, 10));
  const primaryGlow = `hsla(${hsl.h}, ${hsl.s}%, ${hsl.l}%, 0.8)`;
  const secondaryDim = `hsla(${raw.primaryHue + 30}, 60%, 60%, 0.3)`;
  const accentDim = `hsla(${hsl.h}, ${hsl.s}%, ${hsl.l}%, 0.6)`;

  return {
    // Surface — 背景层级
    surface: raw.background,
    surfaceContainer: raw.surface,
    surfaceOverlay: raw.surfaceVariant,
    // 毛玻璃：亮色主题用白玻璃，暗色主题用黑玻璃（根据背景亮度自动判定）
    cardGlassBg:
      hexToHsl(raw.background).l > 50
        ? "rgba(255, 255, 255, 0.7)"
        : "rgba(15, 15, 18, 0.55)",

    // Primary — 主品牌色
    primary: raw.primary,
    primaryHover,
    primaryActive,
    primaryContainer: raw.primaryContainer,
    primaryGlow,
    onPrimary: raw.onPrimary,

    // Secondary — 辅助色
    secondary: raw.secondary,
    secondaryVariant: raw.secondaryContainer,
    secondaryContainer: raw.secondaryContainer,
    secondaryDim,

    // Accent — 强调
    accent: hslToHex(hsl.h, hsl.s, Math.min(hsl.l + 12, 95)),
    accentDim,

    // Outline — 边框
    outline: raw.outline,
    outlineVariant: raw.outlineVariant,

    // Text — 文字
    textPrimary: raw.onBackground,
    textSecondary: raw.onSurfaceVariant,
    textTertiary: raw.onSurfaceVariant,
    textDisabled: raw.onSurfaceVariant,
    textHeading: raw.onBackground,
    textSubtitle: accentDim,

    // Shadow
    shadow: `hsla(${hsl.h}, ${hsl.s}%, ${hsl.l}%, 0.4)`,
    shadowStrong: `hsla(${hsl.h}, ${hsl.s}%, ${hsl.l}%, 0.5)`,

    // Button
    buttonBg: raw.surface,
    buttonText: raw.primary,
    buttonBorder: raw.outlineVariant,
    buttonHoverBorder: primaryHover,
    buttonHoverText: primaryHover,
    buttonHoverShadow: `hsla(${hsl.h}, ${hsl.s}%, ${hsl.l}%, 0.4)`,
    buttonActiveBgStart: raw.primary,
    buttonActiveBgEnd: primaryActive,
    buttonActiveShadow: `hsla(${hsl.h}, ${hsl.s}%, ${hsl.l}%, 0.5)`,

    // Header
    headerGradientStart: raw.primary,
    headerGradientEnd: hslToHex(hsl.h, hsl.s, Math.min(hsl.l + 12, 95)),
    headerTitleShadow: primaryGlow,

    // Footer
    footerGradientBg: raw.background,

    // Chart
    chartGradient: [raw.secondary, raw.primary] as const,
    chartSeries: [
      raw.secondary,
      hslToHex(raw.secondaryHue, 70, 55),
      hslToHex(hsl.h, 80, 45),
      hslToHex(hsl.h, 85, 35),
    ] as const,
    chartStatusGood: raw.secondary,
    chartStatusWarn: hslToHex(raw.secondaryHue, 70, 55),
    chartStatusBad: raw.primary,

    // Loading
    loadingWave: raw.secondary,
  };
}

// ---------------------------------------------------------------------------
// 默认令牌（暖橙主题）
// ---------------------------------------------------------------------------

const defaultSchemes = generateSchemes(DEFAULT_SEED);

/** 亮色主题令牌（当前 UI 视觉） */
export const lightTokens: TokenMap = createTokenMap(defaultSchemes.light);

/** 暗色主题令牌 */
export const darkTokens: TokenMap = createTokenMap(defaultSchemes.dark);
