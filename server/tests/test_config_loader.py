"""
test_config_loader.py — config_loader 单元测试

覆盖映射配置加载、按 source 过滤、MySQL 查询加载、降级策略。
所有测试纯内存运行，不依赖 mapping.yaml 文件存在。
"""

from src.config_loader import (
    load_chart_mapping,
    load_chart_mapping_for_source,
    get_source_configs,
    load_mysql_queries,
    load_data_points,
)

# ══════════════════════════════════════════════════════════════════════════
# 用例 1：每个映射项都带 source 字段
# ══════════════════════════════════════════════════════════════════════════

def test_mapping_items_have_source():
    """load_chart_mapping 返回的 SingleMapping 和 ArrayItem 都应有 source"""
    mapping = load_chart_mapping("chart4")
    assert mapping is not None

    for sm in mapping.single.values():
        assert sm.source in ("iec61850", "mysql"), f"single.{sm.ref} missing source"

    for items in mapping.array.values():
        for item in items:
            assert item.source in ("iec61850", "mysql"), f"array.{item.ref} missing source"


# ══════════════════════════════════════════════════════════════════════════
# 用例 2：按 iec61850 过滤后不含 mysql 条目
# ══════════════════════════════════════════════════════════════════════════

def test_filter_by_source_iec61850():
    """load_chart_mapping_for_source("iec61850") 的结果全为 iec61850"""
    mapping = load_chart_mapping_for_source("iec61850", "chart4")
    assert mapping is not None

    for sm in mapping.single.values():
        assert sm.source == "iec61850"

    for items in mapping.array.values():
        for item in items:
            assert item.source == "iec61850"


# ══════════════════════════════════════════════════════════════════════════
# 用例 3：不存在的 source 返回空映射
# ══════════════════════════════════════════════════════════════════════════

def test_filter_nonexistent_source():
    """source="mqtt" 没有对应条目，返回空 single + 空 array"""
    mapping = load_chart_mapping_for_source("mqtt", "chart4")
    assert mapping is not None
    assert len(mapping.single) == 0
    assert len(mapping.array) == 0


# ══════════════════════════════════════════════════════════════════════════
# 用例 4：get_source_configs 返回正确的 source 列表
# ══════════════════════════════════════════════════════════════════════════

def test_get_source_configs():
    """get_source_configs 至少包含 iec61850"""
    configs = get_source_configs("chart4")
    assert len(configs) >= 1
    sources = {c.source for c in configs}
    assert "iec61850" in sources


# ══════════════════════════════════════════════════════════════════════════
# 用例 5：MySQL queries 字段名正确
# ══════════════════════════════════════════════════════════════════════════

def test_mysql_queries_fields():
    """load_mysql_queries("chart4") 返回正确的字段集合"""
    queries = load_mysql_queries("chart4")
    assert len(queries) == 2
    fields = {q.field for q in queries}
    assert fields == {"total_revenue", "enterprise_count"}

    for q in queries:
        assert q.query.startswith("SELECT"), f"查询语句应以 SELECT 开头: {q.query}"
        assert q.default > 0, f"默认值应为正数: {q.default}"


# ══════════════════════════════════════════════════════════════════════════
# 用例 6：data_points 每个都有 source 字段
# ══════════════════════════════════════════════════════════════════════════

def test_data_points_have_source():
    """load_data_points 返回的每个 DataPointDef 都带 source"""
    points = load_data_points()
    assert len(points) >= 11
    for dp in points:
        assert dp.source in ("iec61850", "mysql"), f"{dp.ref} missing source"
