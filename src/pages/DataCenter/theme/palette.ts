/**
 * 调色板生成器 —— Monet / Material You 风格（自实现，零外部依赖）
 *
 * 种子色 → HSL 色阶 → 双份语义色方案 (亮色 / 暗色)
 * Secondary 色相 = Primary 色相 + 30° 自动偏移
 *
 * 算法参考：
 *   Material Design 3 的 HCT 色彩空间在此简化为 HSL + 色调映射表，
 *   确保亮/暗主题下各语义令牌具有足够的对比度。
 */

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
// HSL 工具
// ---------------------------------------------------------------------------

interface HSL {
  h: number; // 0-360
  s: number; // 0-100
  l: number; // 0-100
}

/** hex → HSL */
function hexToHsl(hex: string): HSL {
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

/** HSL → hex */
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
// 色调映射逻辑
//
// Material You 的核心思想：
//   - 同色相，不同 Tone (亮度) → 不同语义角色
//   - 亮色主题：Tone 高 (near-white) 用于背景，Tone 低 (near-black) 用于文字
//   - 暗色主题：Tone 低 用于背景，Tone 高 用于文字
//   - 色度 (chroma/saturation) 也随 Tone 变化：低 Tone/高 Tone 降低色度避免刺眼
// ---------------------------------------------------------------------------

/** 根据色相、色度和 tone 生成 hex 颜色 */
function tonalColor(hue: number, chroma: number, tone: number): string {
  // tone 0 = 黑, tone 100 = 白 (与 HCT 一致，与 HSL L 同向)
  const lightness = tone;
  // 色度在中间 tone 时最大，两端衰减
  const saturation = chroma * (1 - Math.abs(tone - 50) / 50) * 0.7;
  return hslToHex(hue, Math.min(saturation, 100), Math.max(0, Math.min(100, lightness)));
}

// ---------------------------------------------------------------------------
// 核心生成逻辑
// ---------------------------------------------------------------------------

/**
 * 从种子色生成亮/暗两套完整色方案
 *
 * @param seedHex 种子色 (e.g. "#ea580c" 暖橙, "#4CAF50" 绿)
 */
export function generateSchemes(seedHex: string): {
  light: RawTokens;
  dark: RawTokens;
} {
  // ---- 1. 解析种子色 ----
  const seed = hexToHsl(seedHex);
  const primaryHue = seed.h;
  const primaryChroma = Math.max(seed.s * 1.1, 48);

  // ---- 2. Secondary 色相偏移 ----
  const secondaryHue = (primaryHue + 30) % 360;
  const secondaryChroma = 40;

  // ---- 3. Tertiary 色相 ----
  const tertiaryHue = (primaryHue + 60) % 360;
  const tertiaryChroma = 30;

  // ---- 4. 错误色（红色调） ----
  const errorHue = 4;
  const errorChroma = 60;

  // ---- 5. 中性色色相 = 主色相（保留暖/冷倾向） ----
  const neutralChroma = 4;

  // ---- 6. 便捷函数 ----
  const c = (h: number, chroma: number, tone: number) =>
    tonalColor(h, chroma, tone);

  // ---- 7. 亮色主题 ----
  const light: RawTokens = {
    primary: c(primaryHue, primaryChroma, 40),
    onPrimary: c(primaryHue, 15, 100),
    primaryContainer: c(primaryHue, primaryChroma * 0.5, 90),
    onPrimaryContainer: c(primaryHue, primaryChroma * 0.5, 10),
    secondary: c(secondaryHue, secondaryChroma, 40),
    onSecondary: c(secondaryHue, 15, 100),
    secondaryContainer: c(secondaryHue, secondaryChroma * 0.5, 90),
    onSecondaryContainer: c(secondaryHue, secondaryChroma * 0.5, 10),
    tertiary: c(tertiaryHue, tertiaryChroma, 40),
    onTertiary: c(tertiaryHue, 15, 100),
    tertiaryContainer: c(tertiaryHue, tertiaryChroma * 0.5, 90),
    onTertiaryContainer: c(tertiaryHue, tertiaryChroma * 0.5, 10),
    error: c(errorHue, errorChroma, 40),
    onError: c(errorHue, 15, 100),
    errorContainer: c(errorHue, errorChroma * 0.5, 90),
    onErrorContainer: c(errorHue, errorChroma * 0.5, 10),
    background: c(primaryHue, neutralChroma, 98),
    onBackground: c(primaryHue, neutralChroma, 10),
    surface: c(primaryHue, neutralChroma, 96),
    onSurface: c(primaryHue, neutralChroma, 10),
    surfaceVariant: c(primaryHue, neutralChroma * 1.5, 90),
    onSurfaceVariant: c(primaryHue, neutralChroma * 1.5, 30),
    outline: c(primaryHue, neutralChroma * 1.5, 50),
    outlineVariant: c(primaryHue, neutralChroma, 80),
    shadow: "#000000",
    scrim: "#000000",
    inverseSurface: c(primaryHue, neutralChroma, 20),
    inverseOnSurface: c(primaryHue, neutralChroma, 95),
    inversePrimary: c(primaryHue, primaryChroma * 0.6, 80),
    primaryHue,
    primaryChroma,
    secondaryHue,
  };

  // ---- 8. 暗色主题 ----
  const dark: RawTokens = {
    primary: c(primaryHue, primaryChroma * 0.7, 80),
    onPrimary: c(primaryHue, primaryChroma * 0.4, 20),
    primaryContainer: c(primaryHue, primaryChroma * 0.4, 30),
    onPrimaryContainer: c(primaryHue, primaryChroma * 0.4, 90),
    secondary: c(secondaryHue, secondaryChroma * 0.7, 80),
    onSecondary: c(secondaryHue, secondaryChroma * 0.4, 20),
    secondaryContainer: c(secondaryHue, secondaryChroma * 0.4, 30),
    onSecondaryContainer: c(secondaryHue, secondaryChroma * 0.4, 90),
    tertiary: c(tertiaryHue, tertiaryChroma * 0.7, 80),
    onTertiary: c(tertiaryHue, tertiaryChroma * 0.4, 20),
    tertiaryContainer: c(tertiaryHue, tertiaryChroma * 0.4, 30),
    onTertiaryContainer: c(tertiaryHue, tertiaryChroma * 0.4, 90),
    error: c(errorHue, errorChroma * 0.7, 80),
    onError: c(errorHue, errorChroma * 0.4, 20),
    errorContainer: c(errorHue, errorChroma * 0.4, 30),
    onErrorContainer: c(errorHue, errorChroma * 0.4, 90),
    background: c(primaryHue, neutralChroma, 6),
    onBackground: c(primaryHue, neutralChroma, 90),
    surface: c(primaryHue, neutralChroma, 10),
    onSurface: c(primaryHue, neutralChroma, 90),
    surfaceVariant: c(primaryHue, neutralChroma * 1.5, 30),
    onSurfaceVariant: c(primaryHue, neutralChroma * 1.5, 80),
    outline: c(primaryHue, neutralChroma * 1.5, 60),
    outlineVariant: c(primaryHue, neutralChroma, 30),
    shadow: "#000000",
    scrim: "#000000",
    inverseSurface: c(primaryHue, neutralChroma, 90),
    inverseOnSurface: c(primaryHue, neutralChroma, 20),
    inversePrimary: c(primaryHue, primaryChroma * 0.5, 40),
    primaryHue,
    primaryChroma,
    secondaryHue,
  };

  return { light, dark };
}

/**
 * 种子色
 */
export const DEFAULT_SEED = "#76d6ff";
