/**
 * 语义令牌映射 —— Monet 风格
 *
 * 将 RawTokens (Material Scheme hex) 映射为面向 UI 组件的语义令牌。
 * 组件引用令牌名，不引用具体色值 → 换种子色后零代码改动。
 */

import { generateSchemes, DEFAULT_SEED, type RawTokens } from "./palette";
import { Hct, argbFromHex, hexFromArgb } from "@material/material-color-utilities";

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
// HCT 辅助（用于生成辉光 / 阴影等 CSS 无法直接从 hex 推导的颜色）
// ---------------------------------------------------------------------------

/**
 * 从 RawTokens 构建面向组件的 TokenMap
 *
 * 大部分令牌直接映射 Material Scheme 的语义角色；
 * 辉光 / 阴影 / 按钮渐变等通过 primary 的 HCT 色相动态推算。
 */
export function createTokenMap(raw: RawTokens): TokenMap {
  const primaryHct = Hct.fromInt(argbFromHex(raw.primary));
  const bgHct = Hct.fromInt(argbFromHex(raw.background));

  // Hover：略高的色度和明度
  const hoverHct = Hct.from(
    primaryHct.hue,
    Math.min(primaryHct.chroma + 8, 130),
    Math.min(primaryHct.tone + 8, 95),
  );
  const primaryHover = hexFromArgb(hoverHct.toInt());

  // Active：相同色度，略低的明度
  const activeHct = Hct.from(primaryHct.hue, primaryHct.chroma, Math.max(primaryHct.tone - 5, 10));
  const primaryActive = hexFromArgb(activeHct.toInt());

  // 辉光 / 阴影用 hsla（借用 HCT 的 hue/tone，chroma 映射为近似饱和度）
  const approxSat = Math.min(Math.round(primaryHct.chroma * 1.5), 100);
  const primaryGlow = `hsla(${primaryHct.hue}, ${approxSat}%, ${primaryHct.tone}%, 0.8)`;
  const secondaryDim = `hsla(${raw.primaryHue + 30}, 60%, 60%, 0.3)`;
  const accentDim = `hsla(${primaryHct.hue}, ${approxSat}%, ${primaryHct.tone}%, 0.6)`;

  // Accent：略高的明度
  const accentHct = Hct.from(primaryHct.hue, primaryHct.chroma, Math.min(primaryHct.tone + 12, 95));
  const accent = hexFromArgb(accentHct.toInt());

  return {
    // Surface — 背景层级
    surface: raw.background,
    surfaceContainer: raw.surface,
    surfaceOverlay: raw.surfaceVariant,
    // 毛玻璃：亮色主题用白玻璃，暗色主题用黑玻璃（根据背景亮度自动判定）
    cardGlassBg:
      bgHct.tone > 50
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
    accent,
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
    shadow: `hsla(${primaryHct.hue}, ${approxSat}%, ${primaryHct.tone}%, 0.4)`,
    shadowStrong: `hsla(${primaryHct.hue}, ${approxSat}%, ${primaryHct.tone}%, 0.5)`,

    // Button
    buttonBg: raw.surface,
    buttonText: raw.primary,
    buttonBorder: raw.outlineVariant,
    buttonHoverBorder: primaryHover,
    buttonHoverText: primaryHover,
    buttonHoverShadow: `hsla(${primaryHct.hue}, ${approxSat}%, ${primaryHct.tone}%, 0.4)`,
    buttonActiveBgStart: raw.primary,
    buttonActiveBgEnd: primaryActive,
    buttonActiveShadow: `hsla(${primaryHct.hue}, ${approxSat}%, ${primaryHct.tone}%, 0.5)`,

    // Header
    headerGradientStart: raw.primary,
    headerGradientEnd: accent,
    headerTitleShadow: primaryGlow,

    // Footer
    footerGradientBg: raw.background,

    // Chart — 使用 HCT 生成色阶
    chartGradient: [raw.secondary, raw.primary] as const,
    chartSeries: [
      raw.secondary,
      hexFromArgb(Hct.from(raw.secondaryHue, 50, 55).toInt()),
      hexFromArgb(Hct.from(primaryHct.hue, 60, 45).toInt()),
      hexFromArgb(Hct.from(primaryHct.hue, 65, 35).toInt()),
    ] as const,
    chartStatusGood: raw.secondary,
    chartStatusWarn: hexFromArgb(Hct.from(raw.secondaryHue, 50, 55).toInt()),
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
