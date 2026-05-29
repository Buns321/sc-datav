import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/sc-datav/",
  resolve: {
    alias: {
      "@": resolve("src"),
    },
  },

  /**
   * 开发服务器配置
   *
   * 🔧 proxy 代理配置说明：
   * 前端开发服务器（Vite :5173）会把 /ws 路径的请求代理转发到后端。
   *
   * 例如：前端连接 ws://localhost:5173/ws
   *       → Vite 自动转发到 ws://localhost:8000/ws
   *       → FastAPI 后端处理 WebSocket 连接
   *
   * 好处：
   *   1. 前端不用关心后端端口（避免 CORS 跨域问题）
   *   2. 生产环境同样路径 /ws 可以指向真正的后端域名
   */
  server: {
    proxy: {
      "/ws": {
        target: "ws://localhost:8000",
        ws: true, // 🔧 ws: true = 支持 WebSocket 协议的代理转发
      },
    },
  },
});
