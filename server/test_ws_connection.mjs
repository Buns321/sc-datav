/**
 * 快速测试 WebSocket 连接到后端
 * 运行：node test_ws_connection.mjs
 */
const url = "ws://localhost:8000/ws";
console.log(`正在连接 ${url}...`);

const ws = new WebSocket(url);

ws.addEventListener("open", () => {
  console.log("✅ WebSocket 连接成功！");
});

ws.addEventListener("message", (event) => {
  const data = JSON.parse(event.data);
  console.log(`📩 收到数据: channel=${data.channel}, payload=`, data.payload);
});

ws.addEventListener("error", (event) => {
  console.error("❌ WebSocket 错误:", event.message || "未知错误");
});

ws.addEventListener("close", (event) => {
  console.log(`🔒 WebSocket 已关闭 (code=${event.code})`);
});

// 5 秒后退出
setTimeout(() => {
  console.log("\n⏱️ 测试结束");
  ws.close();
  process.exit(0);
}, 5000);
