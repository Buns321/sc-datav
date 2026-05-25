/**
 * DataCenter 主题公共 API
 *
 * 用法：
 *   import { lightTokens, applyTokens, generateTokens } from "./theme";
 *
 *   // 初始化（在 demo.tsx 中调用一次）
 *   applyTokens(lightTokens);
 *
 *   // 换种子色
 *   const { light } = generateTokens("#4CAF50");
 *   applyTokens(light);
 */

import { lightTokens, darkTokens, createTokenMap, type TokenMap } from "./tokens";
import { generateSchemes, DEFAULT_SEED, type RawTokens } from "./palette";

// ---------------------------------------------------------------------------
// 重导出
// ---------------------------------------------------------------------------

export { lightTokens, darkTokens, DEFAULT_SEED, type TokenMap, type RawTokens };
export { createTokenMap, generateSchemes };

// ---------------------------------------------------------------------------
// CSS 变量注入
// ---------------------------------------------------------------------------

const CSS_VAR_MAP: [string, keyof TokenMap][] = [
  ["surface", "surface"],
  ["surface-container", "surfaceContainer"],
  ["surface-overlay", "surfaceOverlay"],
  ["card-glass-bg", "cardGlassBg"],
  ["primary", "primary"],
  ["primary-hover", "primaryHover"],
  ["primary-active", "primaryActive"],
  ["primary-container", "primaryContainer"],
  ["primary-glow", "primaryGlow"],
  ["on-primary", "onPrimary"],
  ["secondary", "secondary"],
  ["secondary-variant", "secondaryVariant"],
  ["secondary-container", "secondaryContainer"],
  ["secondary-dim", "secondaryDim"],
  ["accent", "accent"],
  ["accent-dim", "accentDim"],
  ["outline", "outline"],
  ["outline-variant", "outlineVariant"],
  ["text-primary", "textPrimary"],
  ["text-secondary", "textSecondary"],
  ["text-tertiary", "textTertiary"],
  ["text-disabled", "textDisabled"],
  ["text-heading", "textHeading"],
  ["text-subtitle", "textSubtitle"],
  ["shadow", "shadow"],
  ["shadow-strong", "shadowStrong"],
  ["button-bg", "buttonBg"],
  ["button-text", "buttonText"],
  ["button-border", "buttonBorder"],
  ["button-hover-border", "buttonHoverBorder"],
  ["button-hover-text", "buttonHoverText"],
  ["button-hover-shadow", "buttonHoverShadow"],
  ["button-active-bg-start", "buttonActiveBgStart"],
  ["button-active-bg-end", "buttonActiveBgEnd"],
  ["button-active-shadow", "buttonActiveShadow"],
  ["header-gradient-start", "headerGradientStart"],
  ["header-gradient-end", "headerGradientEnd"],
  ["header-title-shadow", "headerTitleShadow"],
  ["footer-gradient-bg", "footerGradientBg"],
  ["loading-wave", "loadingWave"],
];

/** 将 TokenMap 中的标量值注入为 CSS 自定义属性 */
export function applyTokens(
  tokenMap: TokenMap,
  target: HTMLElement = document.documentElement,
): void {
  for (const [varName, tokenKey] of CSS_VAR_MAP) {
    target.style.setProperty(`--${varName}`, tokenMap[tokenKey] as string);
  }
}

// ---------------------------------------------------------------------------
// 种子色切换
// ---------------------------------------------------------------------------

/** 运行时更换种子色，返回新的 light / dark TokenMap */
export function generateTokens(seedHex: string): {
  light: TokenMap;
  dark: TokenMap;
} {
  const schemes = generateSchemes(seedHex);
  return {
    light: createTokenMap(schemes.light),
    dark: createTokenMap(schemes.dark),
  };
}
