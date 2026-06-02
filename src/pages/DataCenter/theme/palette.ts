/**
 * 调色板生成器 —— 基于 Google 官方 @material/material-color-utilities
 *
 * 使用 HCT（色相/色度/明度）色彩空间（基于 CAM16 色貌模型），
 * 替代原先的 HSL 模拟方案，生成符合 Material Design 3 标准的色板。
 */

import {
  argbFromHex,
  hexFromArgb,
  Hct,
  SchemeContent,
  MaterialDynamicColors,
  type DynamicColor,
  type DynamicScheme,
} from "@material/material-color-utilities";

// ---------------------------------------------------------------------------
// 类型
// ---------------------------------------------------------------------------

/** Material Scheme 导出的原始令牌（hex 字符串） */
export interface RawTokens {
  primary: string;
  onPrimary: string;
  primaryContainer: string;
  onPrimaryContainer: string;
  secondary: string;
  onSecondary: string;
  secondaryContainer: string;
  onSecondaryContainer: string;
  tertiary: string;
  onTertiary: string;
  tertiaryContainer: string;
  onTertiaryContainer: string;
  error: string;
  onError: string;
  errorContainer: string;
  onErrorContainer: string;
  background: string;
  onBackground: string;
  surface: string;
  onSurface: string;
  surfaceVariant: string;
  onSurfaceVariant: string;
  outline: string;
  outlineVariant: string;
  shadow: string;
  scrim: string;
  inverseSurface: string;
  inverseOnSurface: string;
  inversePrimary: string;
  /** 调色板元数据 */
  primaryHue: number;
  primaryChroma: number;
  secondaryHue: number;
}

// ---------------------------------------------------------------------------
// Material DynamicColors 工具
// ---------------------------------------------------------------------------

/** 单例 —— 缓存 DynamicColor 实例，避免反复构造 */
const mdc = new MaterialDynamicColors();

/** 解析 DynamicColor → hex 字符串 */
function resolve(dc: DynamicColor, scheme: DynamicScheme): string {
  return hexFromArgb(dc.getArgb(scheme));
}

// ---------------------------------------------------------------------------
// 核心生成逻辑（使用官方 HCT 色彩空间）
// ---------------------------------------------------------------------------

/**
 * 从种子色生成亮/暗两套完整色方案
 *
 * @param seedHex 种子色 (e.g. "#76d6ff" 天蓝, "#ea580c" 暖橙)
 */
export function generateSchemes(seedHex: string): {
  light: RawTokens;
  dark: RawTokens;
} {
  const sourceArgb = argbFromHex(seedHex);
  const sourceHct = Hct.fromInt(sourceArgb);

  // SchemeContent：种子色作为 primaryContainer，适合内容主导的场景
  const lightScheme = new SchemeContent(sourceHct, false, 0);
  const darkScheme = new SchemeContent(sourceHct, true, 0);

  // 便捷解析器
  const L = (dc: DynamicColor) => resolve(dc, lightScheme);
  const D = (dc: DynamicColor) => resolve(dc, darkScheme);

  const light: RawTokens = {
    primary: L(mdc.primary()),
    onPrimary: L(mdc.onPrimary()),
    primaryContainer: L(mdc.primaryContainer()),
    onPrimaryContainer: L(mdc.onPrimaryContainer()),
    secondary: L(mdc.secondary()),
    onSecondary: L(mdc.onSecondary()),
    secondaryContainer: L(mdc.secondaryContainer()),
    onSecondaryContainer: L(mdc.onSecondaryContainer()),
    tertiary: L(mdc.tertiary()),
    onTertiary: L(mdc.onTertiary()),
    tertiaryContainer: L(mdc.tertiaryContainer()),
    onTertiaryContainer: L(mdc.onTertiaryContainer()),
    error: L(mdc.error()),
    onError: L(mdc.onError()),
    errorContainer: L(mdc.errorContainer()),
    onErrorContainer: L(mdc.onErrorContainer()),
    background: L(mdc.background()),
    onBackground: L(mdc.onBackground()),
    surface: L(mdc.surface()),
    onSurface: L(mdc.onSurface()),
    surfaceVariant: L(mdc.surfaceVariant()),
    onSurfaceVariant: L(mdc.onSurfaceVariant()),
    outline: L(mdc.outline()),
    outlineVariant: L(mdc.outlineVariant()),
    shadow: L(mdc.shadow()),
    scrim: L(mdc.scrim()),
    inverseSurface: L(mdc.inverseSurface()),
    inverseOnSurface: L(mdc.inverseOnSurface()),
    inversePrimary: L(mdc.inversePrimary()),
    primaryHue: sourceHct.hue,
    primaryChroma: sourceHct.chroma,
    secondaryHue: lightScheme.secondaryPalette.hue,
  };

  const dark: RawTokens = {
    primary: D(mdc.primary()),
    onPrimary: D(mdc.onPrimary()),
    primaryContainer: D(mdc.primaryContainer()),
    onPrimaryContainer: D(mdc.onPrimaryContainer()),
    secondary: D(mdc.secondary()),
    onSecondary: D(mdc.onSecondary()),
    secondaryContainer: D(mdc.secondaryContainer()),
    onSecondaryContainer: D(mdc.onSecondaryContainer()),
    tertiary: D(mdc.tertiary()),
    onTertiary: D(mdc.onTertiary()),
    tertiaryContainer: D(mdc.tertiaryContainer()),
    onTertiaryContainer: D(mdc.onTertiaryContainer()),
    error: D(mdc.error()),
    onError: D(mdc.onError()),
    errorContainer: D(mdc.errorContainer()),
    onErrorContainer: D(mdc.onErrorContainer()),
    background: D(mdc.background()),
    onBackground: D(mdc.onBackground()),
    surface: D(mdc.surface()),
    onSurface: D(mdc.onSurface()),
    surfaceVariant: D(mdc.surfaceVariant()),
    onSurfaceVariant: D(mdc.onSurfaceVariant()),
    outline: D(mdc.outline()),
    outlineVariant: D(mdc.outlineVariant()),
    shadow: D(mdc.shadow()),
    scrim: D(mdc.scrim()),
    inverseSurface: D(mdc.inverseSurface()),
    inverseOnSurface: D(mdc.inverseOnSurface()),
    inversePrimary: D(mdc.inversePrimary()),
    primaryHue: sourceHct.hue,
    primaryChroma: sourceHct.chroma,
    secondaryHue: darkScheme.secondaryPalette.hue,
  };

  return { light, dark };
}

/**
 * 种子色
 */
export const DEFAULT_SEED = "#76d6ff";
