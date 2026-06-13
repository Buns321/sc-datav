"""
test_engine.py — DataEngine 单元测试

覆盖中央数据引擎的两条正式数据路径（iec61850 + mysql）、
多源合并逻辑、降级行为和边界条件。
所有测试纯内存运行，不依赖网络/数据库/WebSocket。
"""

import pytest
from src.engine import DataEngine

# ══════════════════════════════════════════════════════════════════════════
# 辅助：完整的 11 个 IEC 61850 数据对象（缺一不可触发 transformer 输出）
# ══════════════════════════════════════════════════════════════════════════

_ALL_DO_REFS: list[dict] = [
    {"ref": "MMXU1.A.phsA.cVal.mag.f",   "value": 1.02},
    {"ref": "MMXU1.A.phsB.cVal.mag.f",   "value": 0.98},
    {"ref": "MMXU1.A.phsC.cVal.mag.f",   "value": 1.05},
    {"ref": "MMXU1.PhV.phsA.cVal.mag.f", "value": 220.0},
    {"ref": "MMXU1.PhV.phsB.cVal.mag.f", "value": 218.5},
    {"ref": "MMXU1.PhV.phsC.cVal.mag.f", "value": 221.3},
    {"ref": "MMXU1.W.phsA.cVal.mag.f",   "value": 330.0},
    {"ref": "MMXU1.W.phsB.cVal.mag.f",   "value": 325.0},
    {"ref": "MMXU1.W.phsC.cVal.mag.f",   "value": 341.0},
    {"ref": "MMTR1.TotWh.act",           "value": 99608},
]
# 注：total_revenue / enterprise_count 的 DO ref（GGIO1）已迁移到 MySQL，不在 iec61850 范围


# ══════════════════════════════════════════════════════════════════════════
# 用例 1：未收到数据时返回默认降级值
# ══════════════════════════════════════════════════════════════════════════

async def test_default_data_on_init():
    """引擎刚创建、未收到任何数据时，get_current_data 返回默认值"""
    engine = DataEngine()
    data = await engine.get_current_data()
    assert data["total_revenue"] == 99608
    assert data["enterprise_count"] == 7792
    assert len(data["line_data"]) == 10


# ══════════════════════════════════════════════════════════════════════════
# 用例 2：iec61850 部分数据 — transformer 未到齐，不广播
# ══════════════════════════════════════════════════════════════════════════

async def test_iec61850_partial_no_broadcast():
    """只喂 3 个 DO ref，transformer buffer 未到齐，返回 False"""
    engine = DataEngine()
    partial = [
        {"ref": "MMXU1.A.phsA.cVal.mag.f", "value": 1.0},
        {"ref": "MMXU1.A.phsB.cVal.mag.f", "value": 2.0},
        {"ref": "MMXU1.A.phsC.cVal.mag.f", "value": 3.0},
    ]
    result = await engine.push_data("iec61850", partial)
    assert result is False
    cached = await engine.get_current_data()
    assert cached["total_revenue"] == 99608  # 默认值


# ══════════════════════════════════════════════════════════════════════════
# 用例 3：iec61850 完整数据 — 触发广播
# ══════════════════════════════════════════════════════════════════════════

async def test_iec61850_complete_broadcasts():
    """喂齐 10 个 iec61850 来源 DO ref，transformer 输出 line_data"""
    engine = DataEngine()
    result = await engine.push_data("iec61850", _ALL_DO_REFS)
    assert result is True

    cached = await engine.get_current_data()
    assert len(cached["line_data"]) == 10
    # total_revenue / enterprise_count 来自 MySQL，transformer 不输出，engine 填充默认值
    assert cached["total_revenue"] == 99608


# ══════════════════════════════════════════════════════════════════════════
# 用例 4：MySQL 合并后 line_data 不丢失 ★ 最关键
# ══════════════════════════════════════════════════════════════════════════

async def test_mysql_merge_preserves_line_data():
    """MySQL 只覆盖标量字段，line_data 保持 IEC 61850 的值不变"""
    engine = DataEngine()

    # 先推送 iec61850 完整数据（生产级路径，只提供 line_data）
    await engine.push_data("iec61850", _ALL_DO_REFS)
    before = await engine.get_current_data()
    assert len(before["line_data"]) == 10

    # MySQL 推送标量字段
    await engine.push_data("mysql", {
        "total_revenue": 42,
        "enterprise_count": 7,
    })

    cached = await engine.get_current_data()
    # line_data 来自 iec61850 transformer，未被 MySQL 覆盖
    assert len(cached["line_data"]) == 10
    assert cached["total_revenue"] == 42
    assert cached["enterprise_count"] == 7


# ══════════════════════════════════════════════════════════════════════════
# 用例 5：MySQL 合并 — cache 为空时以默认值为底
# ══════════════════════════════════════════════════════════════════════════

async def test_mysql_merge_from_empty_cache():
    """引擎尚无缓存时，MySQL 数据以默认值为底合并"""
    engine = DataEngine()

    await engine.push_data("mysql", {
        "total_revenue": 99,
        "enterprise_count": 55,
    })

    cached = await engine.get_current_data()
    assert cached["total_revenue"] == 99
    assert cached["enterprise_count"] == 55
    assert len(cached["line_data"]) == 10


# ══════════════════════════════════════════════════════════════════════════
# 用例 6：MySQL 数据无变化时跳过广播
# ══════════════════════════════════════════════════════════════════════════

async def test_mysql_no_change_skips_broadcast():
    """MySQL 推送的值与缓存完全一致时，返回 False"""
    engine = DataEngine()

    # 先用 iec61850 设缓存
    await engine.push_data("iec61850", _ALL_DO_REFS)
    cached = await engine.get_current_data()

    # 推送与缓存相同的值
    result = await engine.push_data("mysql", {
        "total_revenue": cached["total_revenue"],
        "enterprise_count": cached["enterprise_count"],
    })
    assert result is False


# ══════════════════════════════════════════════════════════════════════════
# 用例 7：未知 source 返回 False
# ══════════════════════════════════════════════════════════════════════════

async def test_unknown_source_returns_false():
    """未知数据源不会崩溃，返回 False"""
    engine = DataEngine()
    result = await engine.push_data("mqtt", {"some": "data"})
    assert result is False
