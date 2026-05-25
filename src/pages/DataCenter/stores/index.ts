import { create } from "zustand";
import { subscribeWithSelector } from "zustand/middleware";

export type ThemeMode = "light" | "dark";

interface ConfigStore {
  mapPlayComplete: boolean;
  cloud: boolean;
  bar: boolean;
  rotation: boolean;
  heat: boolean;
  mode: boolean;
  /** 当前主题模式 */
  themeMode: ThemeMode;
  /** 种子色（hex），undefined 则使用默认 #9ec8ff */
  seedColor: string | undefined;
  toggle: (key: keyof Omit<ConfigStore, "toggle" | "setThemeMode" | "setSeedColor">) => void;
  setThemeMode: (mode: ThemeMode) => void;
  setSeedColor: (hex: string | undefined) => void;
  reset: () => void;
}

export const useConfigStore = create<ConfigStore>()(
  subscribeWithSelector((set, _, store) => ({
    mapPlayComplete: false,
    cloud: true,
    bar: true,
    rotation: true,
    heat: true,
    mode: true,
    themeMode: "light", // 亮色 / 暗色模式
    seedColor: undefined,
    toggle: (key) => set((s) => ({ [key]: !s[key] })),
    setThemeMode: (mode) => set({ themeMode: mode }),
    setSeedColor: (hex) => set({ seedColor: hex }),
    reset: () => set(store.getInitialState()),
  }))
);
