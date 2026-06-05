# 项目路线图

> 最后更新：2026-06-05

---

## 组件解耦（从 Demo 提取可复用组件）

| 状态 | 任务 | 优先级 | 拆解 | 更新日期 | 备注 |
|------|------|--------|------|----------|------|
| ✅ 已完成 | 组件文字配置化 | 中 | ① 梳理各组件中硬编码的中文字符串<br>② 创建 `src/config/config.ts` 统一文案常量 `CHART_TEXTS`<br>③ chart4 已替换为 config 变量引用（pilot）<br>④ 其他 chart 后续照 chart4 模式逐一替换 | 2026-06-05 | chart4 打样完成，其余图表复用同一模式


## DataCenter 功能增强

| 状态 | 任务 | 优先级 | 拆解 | 更新日期 | 备注 |
|------|------|--------|------|----------|------|
| ✅ 已完成 | 摄像机空闲自动回正 | 中 | ① 监听 OrbitControls 的 `start`/`end` 事件记录最后交互时间<br>② 空闲超过 3 秒后，用 GSAP 将 camera.position 平滑过渡到 `CAMERA_END`<br>③ 回正期间禁用 OrbitControls 避免冲突<br>④ 考虑配合 `CAMERA_INITIAL` 是否要区分"初始位"和"回正位" | 2026-06-02 | 用 `@react-three/drei` 的 OrbitControls + GSAP 实现 |

## 工程化 & 开发体验

| 状态 | 任务 | 优先级 | 拆解 | 更新日期 | 备注 |
|------|------|--------|------|----------|------|
| 📋 计划中 | 项目文档撰写 | 低 | ① 待项目沉淀更成熟后启动<br>② 具体内容/形式待定 | 2026-05-25 | 时机未到，先占位 |
| ✅ 已完成 | 统一配置系统 | 中 | ① 创建 `src/config/config.ts` 单一配置文件，集中管理摄像机、灯光、材质、特效、轨道控制器、特性开关、文案<br>② 8 个组件已改为从 `DC.xxx` 读取参数，消除所有硬编码 magic number<br>③ 删除了旧的散落配置文件 `camera.ts`、`materials.ts`、`texts.ts`<br>④ 按页面/场景覆盖：后续新页面可创建各自的 `config.{page}.ts` | 2026-06-05 | 大一统 config 落地，改参数只需一个文件 |

## 后端

| 状态 | 任务 | 优先级 | 拆解 | 更新日期 | 备注 |
|------|------|--------|------|----------|------|
| 📋 计划中 | Chart1~6 接入后端数据链路 | 高 | ① 扩展 tcp_server 多频道路由（chart1~6）<br>② 创建各 chart 的 transformer（仿 chart4 模式）<br>③ 创建各 chart 的 data 存储模块<br>④ 前端 dataStore + types + demo.tsx + chart.tsx 改从 store 读<br>⑤ TUI 仿真器验证 6 个 chart 实时更新 | 2026-06-05 | 先不做 ICD 外置化，硬编码模式直接复制到 5 个新 chart |
| 📋 计划中 | ICD / 映射配置 YAML 外置化 | 中 | ① 创建 mapping.yaml 统一承载 data_points + charts 映射规则<br>② 创建 config_loader.py（yaml.safe_load + 降级）<br>③ 6 个 transformer 改为从 config_loader 构建映射表<br>④ 仿真器从 config_loader 读 DO ref | 2026-06-05 | 等 chart1~6 全通后再做，一次性提取 |
| 📋 计划中 | 交互式 TUI 仿真器 | 低 | ① 添加 rich 依赖<br>② Rich 面板：数据模式切换 / 调间隔 / 实时显示传感器原始值<br>③ 不涉及 chart 概念，只管数据生成和发送 | 2026-06-05 | 替代命令行脚本；和 chart 接入可并行 |

## 视觉优化

| 状态 | 任务 | 优先级 | 拆解 | 更新日期 | 备注 |
|------|------|--------|------|----------|------|
| 📋 计划中 | 入场动画底部圆圈动效优化 | 低 | ① 调整底部两个旋转环（meshRef1/meshRef2）入场时的缓动函数，从恒定速度改为 ease 曲线<br>② 配合 EntranceReveal GSAP timeline 的时间轴同步<br>③ 考虑加入透明度/缩放渐入效果 | 2026-05-25 | 纯细节打磨，不影响功能 |
| ✅ 已完成 | 浅色模式下毛玻璃背景控件效果调优 | 低 | ① 调整 `cardGlassBg` 亮色模式下的 rgba 参数（当前 `rgba(255,255,255,0.7)`）<br>② 可能需要配合调整 `backdrop-filter: blur(10px)` 的模糊强度<br>③ 分别在 panel 和 tooltip 上验证效果 | 2026-06-02 | 仅调参，不改结构 |
| ✅ 已完成 | 引入 Monet 算法替换现有主题色生成 | 中 | ① 调研 `@material/material-color-utilities` 接入方式<br>② 用 argbFromHex + Hct 替换当前 `colorjs.io` 的 HSL 推算逻辑<br>③ 生成 tonal palette 替代手动调 primaryHover/primaryActive<br>④ 移除 `tokens.ts` 中的手算变体逻辑 | 2026-05-25 | 原 Monet 取色板块归入此处 |
| 📋 计划中 | 解耦后组件动画/设计细节完善 | 低 | ① 等组件解耦完成后再启动<br>② 逐一检查提取后组件的动画流畅度与设计细节<br>③ 具体内容待定 | 2026-05-25 | 依赖解耦任务完成 |
| 📋 计划中 | 3D 模型电流/闪电包裹特效 | 低 | ① 调研实现方案：custom shader / 动态 line geometry / 粒子系统<br>② 围绕 server_room.glb 模型外围生成动态电流效果<br>③ 参考闪电苦力怕的蓝色动态包裹效果 | 2026-05-25 | 有难度，先研究可行性 |
| 📋 计划中 | 3D 模型边缘发光效果 | 高 | ① 调研实现方案：边缘光 shader（fresnel 效果）/ 后处理 bloom<br>② 在 server_room 模型各部件边缘叠加自发光<br>③ 可能需要结合 `MeshStandardMaterial.emissive` + 自定义发光强度控制 | 2026-05-25 | 提升模型视觉层次感 |

## 技术债务

| 状态 | 任务 | 优先级 | 拆解 | 更新日期 | 备注 |
|------|------|--------|------|----------|------|
| 📋 计划中 | 长时间运行稳定性审查（内存泄漏等） | 高 | ① 审查 useEffect/useLayoutEffect 的清除函数是否完备<br>② 审查 Three.js 对象（geometry/material/texture）是否需要手动 dispose<br>③ 审查 GSAP timeline 的 kill/clear 逻辑<br>④ 审查 requestAnimationFrame / setInterval 清理<br>⑤ 审查 OrbitControls 等 drei 组件的事件监听泄漏<br>⑥ 长时间运行压力测试验证 | 2026-05-25 | 大屏经常连开数天，稳定性优先 |
