"""
engine.py — 中央数据引擎

这是整个后端架构的"心脏"。负责：
  1. 接收来自不同消费者的数据（TCP、MySQL、MQTT...）
  2. 在引擎内部完成数据转换、多源合并
  3. 统一通过 WebSocket 广播给所有前端

设计原则：
  - 引擎是唯一的"数据汇聚点" —— 消费者不直接操作 transformer 或 ws_manager
  - 所有数据写入通过 push_data() 统一入口
  - 内部维护最新数据的缓存，供 WebSocket 初始推送使用

数据流（重构后）：
  tcp_consumer ── push_data("iec61850") ──┐
  mysql_consumer ── push_data("mysql") ── DataEngine  ws_manager.broadcast()  前端
  http_api ── get_current_data() ── 缓存

对比旧架构（tcp_server.py 权力过大）：
  tcp_server  Chart4Transformer  chart4_data  ws_manager.broadcast()
  一个函数同时负责"接收 + 转换 + 存储 + 广播"，职责混杂。
"""

import asyncio
import logging
from src.transformers.chart4_transformer import Chart4Transformer
from src.ws_manager import manager as ws_manager
from src.data.chart4_data import update_data as _update_data_store

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# 默认降级数据 —— 引擎刚启动、尚未收到任何数据时使用
# ══════════════════════════════════════════════════════════════════════════

_DEFAULT_DATA: dict = {
    "line_data": [270, 400, 380, 420, 300, 410, 400, 330, 210, 290],
    "total_revenue": 99608,
    "enterprise_count": 7792,
}


class DataEngine:
    """
    中央数据引擎（全局单例）

    使用方式：
        engine = DataEngine()

        # 消费者推送数据
        await engine.push_data("iec61850", data_points)

        # WebSocket 端点获取初始数据
        data = await engine.get_current_data()

    内部结构：
        - _transformer:   Chart4Transformer 实例（buffer 模式，数据到齐才输出）
        - _cache:         最新完整 Chart4Payload dict（供 get_current_data() 使用）
        - _lock:          asyncio.Lock（保证并发安全）
    """

    def __init__(self):
        # ── IEC 61850 数据转换器（buffer 模式） ──
        self._transformer = Chart4Transformer()

        # ── 最新完整数据的缓存 ──
        # None 表示尚未收到任何有效数据
        self._cache: dict | None = None

        # ── 并发锁 ──
        # 多个消费者可能同时调用 push_data()，需要保护 _cache 和 _transformer
        self._lock = asyncio.Lock()

    # ══════════════════════════════════════════════════════════════════════
    # 公共入口
    # ══════════════════════════════════════════════════════════════════════

    async def push_data(self, source: str, data) -> bool:
        """
        消费者统一数据推送入口。

        参数:
            source: 数据来源标识 — "iec61850" | "mysql"
            data:   数据内容，格式因 source 而异：
                    - "iec61850":      list[dict]  数据对象列表
                    - "mysql":         dict        字段值的映射

        返回:
            True  — 数据已处理并广播
            False — 数据已接收但未触发广播（例如 transformer 数据未到齐）
        """
        async with self._lock:
            return await self._dispatch(source, data)

    async def get_current_data(self) -> dict:
        """
        获取最新的 Chart4 数据快照。

        用途：新 WebSocket 连接建立后，立即推送当前缓存的数据，
             避免前端首屏空白等待。

        返回:
            dict: Chart4Payload 的字典形式（副本，安全对外）
        """
        async with self._lock:
            if self._cache is not None:
                return self._cache.copy()
        # 引擎尚未收到任何数据，返回默认降级值
        return _DEFAULT_DATA.copy()

    # ══════════════════════════════════════════════════════════════════════
    # 内部分发
    # ══════════════════════════════════════════════════════════════════════

    async def _dispatch(self, source: str, data) -> bool:
        """根据 source 分发到对应的内部处理器"""
        if source == "iec61850":
            return await self._handle_iec61850(data)
        elif source == "mysql":
            return await self._handle_mysql(data)
        else:
            logger.warning(f" 未知数据源: {source}")
            return False

    # ══════════════════════════════════════════════════════════════════════
    # 处理器: iec61850（IEC 61850 网关  TCP  数据对象列表）
    # ══════════════════════════════════════════════════════════════════════

    async def _handle_iec61850(self, data_points: list[dict]) -> bool:
        """
        处理来自 IEC 61850 网关的原始数据对象。

        流程:
            1. 喂入 Chart4Transformer（buffer 模式）
            2. 如果数据到齐  输出 Chart4Payload
            3. 更新缓存 + 广播
            4. 如果未到齐  返回 False，等待后续 batch
        """
        result = self._transformer.feed(data_points)

        if result is None:
            # 数据未到齐，等待后续 batch（不广播）
            return False

        # 数据到齐：存入缓存并广播
        payload_dict = result.model_dump()
        self._cache = payload_dict

        # 同时更新旧的数据层（保持向后兼容）
        await _update_data_store(payload_dict)

        await self._broadcast(payload_dict)
        logger.info(
            f" [iec61850] 数据到齐并广播: "
            f"line_data={result.line_data[:3]}..., "
            f"total_revenue={result.total_revenue}, "
            f"enterprise_count={result.enterprise_count}"
        )
        return True

    # ══════════════════════════════════════════════════════════════════════
    # 处理器: mysql（MySQL 轮询  标量统计值）
    # ══════════════════════════════════════════════════════════════════════

    async def _handle_mysql(self, data: dict) -> bool:
        """
        处理 MySQL 轮询结果并合并到现有缓存。

        MySQL 提供的是标量统计值（如 total_revenue, enterprise_count），
        而 line_data 来自 IEC 61850 实时传感器。
        合并策略:
            - 如果 _cache 已有数据（含 iec61850 的 line_data） 用 MySQL 值覆盖标量字段
            - 如果 _cache 为空  以默认值为底，填入 MySQL 值（line_data 使用默认值）

        参数:
            data: dict — 字段名值，例如 {"total_revenue": 99608, "enterprise_count": 7792}
        """
        # 以默认值或现有缓存为基础
        base = _DEFAULT_DATA.copy()
        if self._cache is not None:
            base = self._cache.copy()

        # 用 MySQL 结果覆盖对应字段
        merged = False
        for field, value in data.items():
            if field in base:
                if base[field] != value:
                    merged = True
                    base[field] = value
                    logger.info(f"   [mysql] {field}: {base.get(field, '?')}  {value}")
            else:
                logger.warning(f" [mysql] 未知字段 {field}，已忽略")

        if not merged:
            logger.debug(" [mysql] 数据无变化，跳过广播")
            return False

        # 更新缓存和广播
        self._cache = base
        await _update_data_store(base)
        await self._broadcast(base)
        logger.info(
            f" [mysql] 多源合并后广播: "
            f"total_revenue={base.get('total_revenue')}, "
            f"enterprise_count={base.get('enterprise_count')}"
        )
        return True

    # ══════════════════════════════════════════════════════════════════════
    # 广播
    # ══════════════════════════════════════════════════════════════════════

    async def _broadcast(self, payload: dict) -> None:
        """构造标准消息并通过 WebSocket 广播给所有前端"""
        msg = {
            "type": "data",
            "channel": "chart4",
            "payload": payload,
            "timestamp": "",
        }
        await ws_manager.broadcast(msg)
