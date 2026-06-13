"""
chart4_transformer.py — IEC 61850 DO ref → Chart4 前端字段

数据流：
  网关 → tcp_server → chart4_transformer.feed() → Chart4Payload → data store → WebSocket → 前端

核心设计：
  - SINGLE_MAPPING:  1 个 DO ref → 1 个 Chart4 标量字段
  - ARRAY_MAPPING:   多个 DO ref → line_data 数组
  - buffer 模式:     内部缓存 DO ref 最新值，所有字段到齐才输出
  - 品质字段:        当前仅记录不校验，后续可扩展过滤逻辑

写给嵌入式开发者：
  类比 Modbus 寄存器表 → SCADA 系统画面的"点表"。
  这里的映射表 = 把 IED 的每个数据对象分配到前端图表的对应位置。
"""

import logging
from typing import Protocol, Callable, Any
from src.models.chart4 import Chart4Payload
from src.iec61850.config import DATA_POINT_DEFS

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# 类型
# ══════════════════════════════════════════════════════════════════════════

class Transformer(Protocol):
    """Transformer 接口 —— 后续新增 Chart1~Chart6 各自实现"""
    def feed(self, data_points: list[dict]) -> Any | None:
        """喂入一批原始数据对象，如果数据齐全则返回转换结果，否则 None"""
        ...


# ══════════════════════════════════════════════════════════════════════════
# Chart4Transformer 实现
# ══════════════════════════════════════════════════════════════════════════
#
# 映射表来源：server/config/mapping.yaml → config_loader.load_chart_mapping("chart4")
# 如果 YAML 不可用，config_loader 内置 fallback。
# ══════════════════════════════════════════════════════════════════════════

from src.config_loader import load_chart_mapping_for_source, get_all_needed_refs_for_source

# ── 编译 transform 表达式 ──
def _compile_transform(expr: str) -> Callable[[float], int | float]:
    """将 YAML 中的 transform 字符串编译为可调用函数。v = 原始 DO ref 值"""
    safe_builtins = {"abs": abs, "int": int, "round": round, "min": min, "max": max}
    try:
        return eval(f"lambda v: {expr}", {"__builtins__": safe_builtins}, {})
    except Exception:
        logger.warning(f"无法编译 transform 表达式: {expr}，使用恒等")
        return lambda v: v

# ── 从 config_loader 构建映射表（仅 iec61850 来源）──
_mapping = load_chart_mapping_for_source("iec61850", "chart4")
if _mapping is None:
    raise RuntimeError("chart4 iec61850 mapping not found in mapping.yaml and no fallback")

_SINGLE_MAPPING: dict[str, dict[str, str | Callable[[float], int | float]]] = {
    field: {"ref": sm.ref, "transform": _compile_transform(sm.transform)}
    for field, sm in _mapping.single.items()
}

_LINE_DATA_ITEMS: list[tuple[str, float]] = []
for field_name, items in _mapping.array.items():
    for item in items:
        _LINE_DATA_ITEMS.append((item.ref, item.scale))

_ALL_NEEDED_REFS: set[str] = get_all_needed_refs_for_source("iec61850")


class Chart4Transformer:
    """
    IEC 61850 数据对象 → Chart4 前端图表数据

    内部维护一个 DO ref → 最新值的 buffer。
    每次调用 feed() 更新 buffer，检查是否需要的数据到齐了，
    到齐 → 输出 Chart4Payload
    未到齐 → 返回 None（等待更多数据）

    使用方式：
        transformer = Chart4Transformer()
        result = transformer.feed(data_points)
        if result is not None:
            await update_data(result.model_dump())
            await ws_manager.broadcast(...)
    """

    def __init__(self):
        # DO ref → 最新 value（float）
        self._buffer: dict[str, float] = {}

        # 可选：记录最近一批数据对象中的品质字段
        # DO ref → quality string (e.g. "0x0000")
        # 后续可扩展品质过滤逻辑
        self._quality: dict[str, str] = {}

    def feed(self, data_points: list[dict]) -> Chart4Payload | None:
        """
        喂入一批 IEC 61850 数据对象。

        参数:
            data_points: 由网关发出的结构化数据列表，每个元素格式：
                {"ref": "MMTR1.TotWh.act", "value": 996.08, "quality": "0x0000", ...}

        返回:
            Chart4Payload — 所需数据到齐，输出转换结果
            None           — 数据未到齐，等待后续 batch
        """
        # ── 步骤 1: 更新 buffer ──
        for dp in data_points:
            ref = dp.get("ref", "")
            value = dp.get("value")
            quality = dp.get("quality", "")

            if not ref or value is None:
                continue

            try:
                self._buffer[ref] = float(value)
                if quality:
                    self._quality[ref] = quality
            except (ValueError, TypeError):
                logger.warning(f"无法将 DO ref [{ref}] 的值转为 float: {value}")
                continue

        # ── 步骤 2: 检查所有需要的 DO ref 是否到齐 ──
        if not self._ready():
            missing = _ALL_NEEDED_REFS - set(self._buffer.keys())
            logger.debug(f"⌛ 等待更多 DO ref: {', '.join(sorted(missing))}")
            return None

        # ── 步骤 3: 构建 Chart4Payload ──
        try:
            payload_dict: dict[str, Any] = {}

            # 3a. 标量字段
            for field, cfg in _SINGLE_MAPPING.items():
                ref = cfg["ref"]
                raw = self._buffer[ref]
                transform: Callable = cfg["transform"]
                payload_dict[field] = transform(raw)

            # 3b. line_data 数组 — 每个 DO ref × 缩放系数，统一量级
            payload_dict["line_data"] = [
                int(self._buffer[ref] * scale) for ref, scale in _LINE_DATA_ITEMS
            ]

            # 3c. Pydantic 校验
            payload = Chart4Payload(**payload_dict)

            logger.info(
                f"Transformer 输出: "
                f"line_data={payload.line_data[:3]}..., "
                f"total_revenue={payload.total_revenue}, "
                f"enterprise_count={payload.enterprise_count}"
            )
            return payload

        except Exception as e:
            logger.error(f"Transformer 构建 Chart4Payload 失败: {e}")
            return None

    def _ready(self) -> bool:
        """检查 buffer 中是否已有所有需要的 DO ref 值"""
        needed = _ALL_NEEDED_REFS
        have = set(self._buffer.keys())
        return needed.issubset(have)

    def reset(self):
        """清空 buffer，可用于连接断开后重新开始累积"""
        self._buffer.clear()
        self._quality.clear()
