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
    source: str = "iec61850"            # 数据来源: "iec61850" | "mysql"


@dataclass
class SingleMapping:
    """标量映射规则: 一个 DO ref → 一个 Chart 字段"""
    ref: str
    transform: str
    source: str = "iec61850"            # 数据来源: "iec61850" | "mysql"


@dataclass
class ArrayItem:
    """数组映射规则: 一个 DO ref（可乘缩放系数）→ 数组中的一个元素"""
    ref: str
    scale: float
    source: str = "iec61850"            # 数据来源: "iec61850" | "mysql"


@dataclass
class ChartMapping:
    """一个图表的完整映射规则"""
    single: dict[str, SingleMapping]    # 字段名  标量映射
    array: dict[str, list[ArrayItem]]   # 数组字段名  ArrayItem 列表


@dataclass
class SourceConfig:
    """按数据来源拆分的配置集"""
    source: str                         # 数据来源标识
    single: dict[str, SingleMapping]    # 属于该来源的标量映射
    array: dict[str, list[ArrayItem]]   # 属于该来源的数组映射


@dataclass
class MysqlQuery:
    """MySQL 轮询查询定义（供 mysql_consumer 使用）"""
    field: str           # 对应的 Chart4 字段名（如 "total_revenue"）
    query: str           # SQL 查询语句
    transform: str = "v" # lambda 表达式（v = 查询结果第一列的值）
    default: float = 0   # 查询失败时的默认值


# ══════════════════════════════════════════════════════════════════════════
# YAML 加载
# ══════════════════════════════════════════════════════════════════════════

_YAML_PATH = Path(__file__).parent.parent / "config" / "mapping.yaml"


def _load_yaml() -> dict | None:
    """尝试加载 mapping.yaml，失败返回 None"""
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML 未安装，使用内置默认映射")
        return None

    if not _YAML_PATH.exists():
        logger.warning(f"{_YAML_PATH} 不存在，使用内置默认映射")
        return None

    try:
        with open(_YAML_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"解析 {_YAML_PATH} 失败: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════
# 内置默认值（mapping.yaml 不可用时的 fallback）
# ══════════════════════════════════════════════════════════════════════════

_DEFAULT_DATA_POINTS: list[DataPointDef] = [
    DataPointDef("MMXU1.A.phsA.cVal.mag.f",   "A 相电流",      1.02,   "kA",   source="iec61850"),
    DataPointDef("MMXU1.A.phsB.cVal.mag.f",   "B 相电流",      0.98,   "kA",   source="iec61850"),
    DataPointDef("MMXU1.A.phsC.cVal.mag.f",   "C 相电流",      1.05,   "kA",   source="iec61850"),
    DataPointDef("MMXU1.PhV.phsA.cVal.mag.f", "A 相电压",      220.0,  "kV",   source="iec61850"),
    DataPointDef("MMXU1.PhV.phsB.cVal.mag.f", "B 相电压",      218.5,  "kV",   source="iec61850"),
    DataPointDef("MMXU1.PhV.phsC.cVal.mag.f", "C 相电压",      221.3,  "kV",   source="iec61850"),
    DataPointDef("MMXU1.W.phsA.cVal.mag.f",   "A 相有功功率",  330.0,  "MW",   source="iec61850"),
    DataPointDef("MMXU1.W.phsB.cVal.mag.f",   "B 相有功功率",  325.0,  "MW",   source="iec61850"),
    DataPointDef("MMXU1.W.phsC.cVal.mag.f",   "C 相有功功率",  341.0,  "MW",   source="iec61850"),
    DataPointDef("MMTR1.TotWh.act",           "总有功电能",    99608,  "MWh",  source="iec61850"),
    DataPointDef("GGIO1.IntIn1.stVal",        "企业数量指示",  7792,   "个",   source="iec61850"),
]


_DEFAULT_CHART4_MAPPING = ChartMapping(
    single={
        "total_revenue":    SingleMapping("MMTR1.TotWh.act",    "round(v / 10000)", source="mysql"),
        "enterprise_count": SingleMapping("GGIO1.IntIn1.stVal", "int(v)",            source="mysql"),
    },
    array={
        "line_data": [
            ArrayItem("MMXU1.A.phsA.cVal.mag.f",   265,   source="iec61850"),
            ArrayItem("MMXU1.A.phsB.cVal.mag.f",   408,   source="iec61850"),
            ArrayItem("MMXU1.A.phsC.cVal.mag.f",   362,   source="iec61850"),
            ArrayItem("MMXU1.PhV.phsA.cVal.mag.f", 1.9,   source="iec61850"),
            ArrayItem("MMXU1.PhV.phsB.cVal.mag.f", 1.4,   source="iec61850"),
            ArrayItem("MMXU1.PhV.phsC.cVal.mag.f", 1.9,   source="iec61850"),
            ArrayItem("MMXU1.W.phsA.cVal.mag.f",   1.2,   source="iec61850"),
            ArrayItem("MMXU1.W.phsB.cVal.mag.f",   1.0,   source="iec61850"),
            ArrayItem("MMXU1.W.phsC.cVal.mag.f",   0.6,   source="iec61850"),
            ArrayItem("MMTR1.TotWh.act",           0.003, source="iec61850"),
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
                source=str(p.get("source", "iec61850")),
            )
            for p in points
        ]
    except Exception as e:
        logger.error(f"解析 data_points 失败: {e}，降级到默认")
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
            logger.warning(f"mapping.yaml 中未定义 {chart_name}，跳过")
            return None

        # 解析 single mappings
        single: dict[str, SingleMapping] = {}
        for field_name, cfg in chart_cfg.get("single", {}).items():
            single[field_name] = SingleMapping(
                ref=str(cfg["ref"]),
                transform=str(cfg.get("transform", "v")),
                source=str(cfg.get("source", "iec61850")),
            )

        # 解析 array mappings
        array: dict[str, list[ArrayItem]] = {}
        for field_name, items in chart_cfg.get("array", {}).items():
            array[field_name] = [
                ArrayItem(
                    ref=str(i["ref"]),
                    scale=float(i.get("scale", 1.0)),
                    source=str(i.get("source", "iec61850")),
                )
                for i in items
            ]

        return ChartMapping(single=single, array=array)

    except Exception as e:
        logger.error(f"解析 charts.{chart_name} 失败: {e}，降级到默认")
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


def get_all_needed_refs_for_source(source: str) -> set[str]:
    """获取指定数据源所需的所有 DO ref 集合"""
    refs: set[str] = set()
    for chart_name in ("chart4",):
        mapping = load_chart_mapping(chart_name)
        if mapping is None:
            continue
        for sm in mapping.single.values():
            if sm.source == source:
                refs.add(sm.ref)
        for items in mapping.array.values():
            for item in items:
                if item.source == source:
                    refs.add(item.ref)
    return refs


def load_chart_mapping_for_source(source: str, chart_name: str) -> ChartMapping | None:
    """
    加载指定图表的映射规则，仅保留属于指定数据源的条目。

    返回的 ChartMapping 中只包含 source 匹配的 single 和 array 条目。
    如果没有匹配项，single 和 array 为空字典。
    如果 chart 未定义，返回 None。
    """
    full_mapping = load_chart_mapping(chart_name)
    if full_mapping is None:
        return None

    filtered_single = {
        field: sm
        for field, sm in full_mapping.single.items()
        if sm.source == source
    }
    filtered_array: dict[str, list[ArrayItem]] = {}
    for field_name, items in full_mapping.array.items():
        filtered_items = [item for item in items if item.source == source]
        if filtered_items:
            filtered_array[field_name] = filtered_items

    return ChartMapping(single=filtered_single, array=filtered_array)


def get_source_configs(chart_name: str) -> list[SourceConfig]:
    """
    将指定图表的映射配置按数据来源拆分。

    返回 SourceConfig 列表，每个元素包含该来源的 single 和 array 映射。
    可用于消费者（tcp_consumer、mysql_consumer）获取各自需要的配置子集。
    """
    full_mapping = load_chart_mapping(chart_name)
    if full_mapping is None:
        return []

    # 收集所有出现的 source 值
    sources: set[str] = set()
    for sm in full_mapping.single.values():
        sources.add(sm.source)
    for items in full_mapping.array.values():
        for item in items:
            sources.add(item.source)

    # 为每个 source 构建配置子集
    result: list[SourceConfig] = []
    for src in sorted(sources):
        filtered_single = {
            field: sm
            for field, sm in full_mapping.single.items()
            if sm.source == src
        }
        filtered_array: dict[str, list[ArrayItem]] = {}
        for field_name, items in full_mapping.array.items():
            filtered_items = [item for item in items if item.source == src]
            if filtered_items:
                filtered_array[field_name] = filtered_items
        result.append(SourceConfig(
            source=src,
            single=filtered_single,
            array=filtered_array,
        ))

    return result


# ══════════════════════════════════════════════════════════════════════════
# MySQL 查询加载
# ══════════════════════════════════════════════════════════════════════════

_DEFAULT_MYSQL_QUERIES: dict[str, list[MysqlQuery]] = {
    "chart4": [
        MysqlQuery(
            field="total_revenue",
            query="SELECT total FROM revenue_table ORDER BY id DESC LIMIT 1",
            transform="round(v / 10000)",
            default=99608,
        ),
        MysqlQuery(
            field="enterprise_count",
            query="SELECT count FROM enterprise_table ORDER BY id DESC LIMIT 1",
            transform="int(v)",
            default=7792,
        ),
    ],
}


def load_mysql_queries(chart_name: str) -> list[MysqlQuery]:
    """
    加载指定图表的 MySQL 轮询查询定义。

    从 mapping.yaml 的 mysql_queries 段读取。
    如果 YAML 不可用或该 chart 未定义，返回内置默认值。

    使用方式:
        queries = load_mysql_queries("chart4")
        for q in queries:
            result = await cursor.execute(q.query)
            value = transform(result[0])
    """
    data = _load_yaml()
    if data is None:
        return _DEFAULT_MYSQL_QUERIES.get(chart_name, [])

    try:
        mysql_section = data.get("mysql_queries", {})
        chart_queries = mysql_section.get(chart_name, [])
        if not chart_queries:
            logger.warning(f"  mysql_queries.{chart_name} 未定义，使用默认值")
            return _DEFAULT_MYSQL_QUERIES.get(chart_name, [])

        return [
            MysqlQuery(
                field=str(q["field"]),
                query=str(q["query"]),
                transform=str(q.get("transform", "v")),
                default=float(q.get("default", 0)),
            )
            for q in chart_queries
        ]
    except Exception as e:
        logger.error(f" 解析 mysql_queries.{chart_name} 失败: {e}，降级到默认")
        return _DEFAULT_MYSQL_QUERIES.get(chart_name, [])
