"""
config_loader.py — 读取 mapping.yaml，提供数据点定义和图表映射规则。

使用方式:
    from src.config_loader import load_data_points, load_chart_mapping

    data_points = load_data_points()          # → list[DataPointDef]
    mapping = load_chart_mapping("chart4")    # → dict | None

降级策略:
    如果 mapping.yaml 不存在或解析失败，返回内置默认值。
"""

import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
# 类型
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class DataPointDef:
    """一条传感器数据点的定义"""
    ref: str
    label: str
    default: float
    unit: str


@dataclass
class SingleMapping:
    """标量映射规则: 一个 DO ref → 一个 Chart 字段"""
    ref: str
    transform: str


@dataclass
class ArrayItem:
    """数组映射规则: 一个 DO ref（可乘缩放系数）→ 数组中的一个元素"""
    ref: str
    scale: float


@dataclass
class ChartMapping:
    """一个图表的完整映射规则"""
    single: dict[str, SingleMapping]    # 字段名 → 标量映射
    array: dict[str, list[ArrayItem]]   # 数组字段名 → ArrayItem 列表


# ══════════════════════════════════════════════════════════════════════════
# YAML 加载
# ══════════════════════════════════════════════════════════════════════════

_YAML_PATH = Path(__file__).parent.parent / "config" / "mapping.yaml"


def _load_yaml() -> dict | None:
    """尝试加载 mapping.yaml，失败返回 None"""
    try:
        import yaml
    except ImportError:
        logger.warning("⚠️  PyYAML 未安装，使用内置默认映射")
        return None

    if not _YAML_PATH.exists():
        logger.warning(f"⚠️  {_YAML_PATH} 不存在，使用内置默认映射")
        return None

    try:
        with open(_YAML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"❌ 解析 {_YAML_PATH} 失败: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# 内置默认值（mapping.yaml 不可用时的 fallback）
# ══════════════════════════════════════════════════════════════════════════

_DEFAULT_DATA_POINTS: list[DataPointDef] = [
    DataPointDef("MMXU1.A.phsA.cVal.mag.f",   "A 相电流",      1.02,   "kA"),
    DataPointDef("MMXU1.A.phsB.cVal.mag.f",   "B 相电流",      0.98,   "kA"),
    DataPointDef("MMXU1.A.phsC.cVal.mag.f",   "C 相电流",      1.05,   "kA"),
    DataPointDef("MMXU1.PhV.phsA.cVal.mag.f", "A 相电压",      220.0,  "kV"),
    DataPointDef("MMXU1.PhV.phsB.cVal.mag.f", "B 相电压",      218.5,  "kV"),
    DataPointDef("MMXU1.PhV.phsC.cVal.mag.f", "C 相电压",      221.3,  "kV"),
    DataPointDef("MMXU1.W.phsA.cVal.mag.f",   "A 相有功功率",  330.0,  "MW"),
    DataPointDef("MMXU1.W.phsB.cVal.mag.f",   "B 相有功功率",  325.0,  "MW"),
    DataPointDef("MMXU1.W.phsC.cVal.mag.f",   "C 相有功功率",  341.0,  "MW"),
    DataPointDef("MMTR1.TotWh.act",           "总有功电能",    99608,  "MWh"),
    DataPointDef("GGIO1.IntIn1.stVal",        "企业数量指示",  7792,   "个"),
]


_DEFAULT_CHART4_MAPPING = ChartMapping(
    single={
        "total_revenue":    SingleMapping("MMTR1.TotWh.act",    "round(v / 10000)"),
        "enterprise_count": SingleMapping("GGIO1.IntIn1.stVal", "int(v)"),
    },
    array={
        "line_data": [
            ArrayItem("MMXU1.A.phsA.cVal.mag.f",   265),
            ArrayItem("MMXU1.A.phsB.cVal.mag.f",   408),
            ArrayItem("MMXU1.A.phsC.cVal.mag.f",   362),
            ArrayItem("MMXU1.PhV.phsA.cVal.mag.f", 1.9),
            ArrayItem("MMXU1.PhV.phsB.cVal.mag.f", 1.4),
            ArrayItem("MMXU1.PhV.phsC.cVal.mag.f", 1.9),
            ArrayItem("MMXU1.W.phsA.cVal.mag.f",   1.2),
            ArrayItem("MMXU1.W.phsB.cVal.mag.f",   1.0),
            ArrayItem("MMXU1.W.phsC.cVal.mag.f",   0.6),
            ArrayItem("MMTR1.TotWh.act",           0.003),
        ]
    }
)


# ══════════════════════════════════════════════════════════════════════════
# 公共 API
# ══════════════════════════════════════════════════════════════════════════

def load_data_points() -> list[DataPointDef]:
    """加载传感器数据点列表。YAML 不可用时返回内置默认值。"""
    data = _load_yaml()
    if data is None:
        return list(_DEFAULT_DATA_POINTS)

    try:
        points = data.get("data_points", [])
        return [
            DataPointDef(
                ref=str(p["ref"]),
                label=str(p.get("label", "")),
                default=float(p.get("default", 0)),
                unit=str(p.get("unit", "")),
            )
            for p in points
        ]
    except Exception as e:
        logger.error(f"❌ 解析 data_points 失败: {e}，降级到默认")
        return list(_DEFAULT_DATA_POINTS)


def load_chart_mapping(chart_name: str) -> ChartMapping | None:
    """加载指定图表的映射规则。YAML 不可用或该 chart 未定义时返回默认值。"""
    data = _load_yaml()
    if data is None:
        if chart_name == "chart4":
            return _DEFAULT_CHART4_MAPPING
        return None

    try:
        charts = data.get("charts", {})
        chart_cfg = charts.get(chart_name)
        if chart_cfg is None:
            logger.warning(f"⚠️  mapping.yaml 中未定义 {chart_name}，跳过")
            return None

        # 解析 single mappings
        single: dict[str, SingleMapping] = {}
        for field_name, cfg in chart_cfg.get("single", {}).items():
            single[field_name] = SingleMapping(
                ref=str(cfg["ref"]),
                transform=str(cfg.get("transform", "v")),
            )

        # 解析 array mappings
        array: dict[str, list[ArrayItem]] = {}
        for field_name, items in chart_cfg.get("array", {}).items():
            array[field_name] = [
                ArrayItem(ref=str(i["ref"]), scale=float(i.get("scale", 1.0)))
                for i in items
            ]

        return ChartMapping(single=single, array=array)

    except Exception as e:
        logger.error(f"❌ 解析 charts.{chart_name} 失败: {e}，降级到默认")
        if chart_name == "chart4":
            return _DEFAULT_CHART4_MAPPING
        return None


def get_all_needed_refs() -> set[str]:
    """获取所有 chart 所需的所有 DO ref 集合（供 transformer 判断数据是否到齐）"""
    refs: set[str] = set()
    for chart_name in ("chart4",):  # 后续扩展：加 "chart1", "chart2" ...
        mapping = load_chart_mapping(chart_name)
        if mapping is None:
            continue
        for sm in mapping.single.values():
            refs.add(sm.ref)
        for items in mapping.array.values():
            for item in items:
                refs.add(item.ref)
    return refs
