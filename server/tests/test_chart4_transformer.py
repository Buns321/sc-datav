"""
test_chart4_transformer.py — Chart4Transformer 单元测试

覆盖 buffer 累积、数据到齐判断、reset、边界输入处理。
"""

import pytest
from src.transformers.chart4_transformer import Chart4Transformer

# ══════════════════════════════════════════════════════════════════════════
# 辅助：完整的 11 个 DO ref
# ══════════════════════════════════════════════════════════════════════════

_ALL_REFS: list[dict] = [
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
# 注：共 10 个 iec61850 来源 DO ref（GGIO1 已迁移到 MySQL）


# ══════════════════════════════════════════════════════════════════════════
# 用例 1：只喂部分 DO ref — 返回 None
# ══════════════════════════════════════════════════════════════════════════

def test_feed_partial_returns_none():
    """只喂 3 个 DO ref，buffer 未到齐，返回 None"""
    t = Chart4Transformer()
    partial = [
        {"ref": "MMXU1.A.phsA.cVal.mag.f", "value": 1.0},
        {"ref": "MMXU1.A.phsB.cVal.mag.f", "value": 2.0},
        {"ref": "MMXU1.A.phsC.cVal.mag.f", "value": 3.0},
    ]
    result = t.feed(partial)
    assert result is None


# ══════════════════════════════════════════════════════════════════════════
# 用例 2：喂齐全部 11 个 DO ref — 输出 Chart4Payload
# ══════════════════════════════════════════════════════════════════════════

def test_feed_complete_returns_payload():
    """一次性喂齐 11 个 DO ref，返回非 None 的 Chart4Payload"""
    t = Chart4Transformer()
    result = t.feed(_ALL_REFS)
    assert result is not None
    assert len(result.line_data) == 10
    assert isinstance(result.total_revenue, int)
    assert isinstance(result.enterprise_count, int)


# ══════════════════════════════════════════════════════════════════════════
# 用例 3：reset 清空 buffer
# ══════════════════════════════════════════════════════════════════════════

def test_reset_clears_buffer():
    """reset 后 buffer 清空，再喂部分数据仍返回 None"""
    t = Chart4Transformer()

    # 先喂 9 个（差 1 个才齐）
    result1 = t.feed(_ALL_REFS[:9])
    assert result1 is None

    # reset 清空
    t.reset()

    # 再喂 3 个，应该又不够
    result2 = t.feed(_ALL_REFS[:3])
    assert result2 is None


# ══════════════════════════════════════════════════════════════════════════
# 用例 4：非法值不崩溃
# ══════════════════════════════════════════════════════════════════════════

def test_invalid_value_not_crash():
    """无法转为 float 的值不应导致崩溃"""
    t = Chart4Transformer()
    data = [
        {"ref": "MMXU1.A.phsA.cVal.mag.f", "value": "not_a_number"},
        {"ref": "MMXU1.A.phsB.cVal.mag.f", "value": None},
        {"ref": "MMXU1.A.phsC.cVal.mag.f", "value": 3.0},
    ]
    # 不应抛异常
    result = t.feed(data)
    assert result is None


# ══════════════════════════════════════════════════════════════════════════
# 用例 5：跨 batch 累积 — 分批喂入最终到齐
# ══════════════════════════════════════════════════════════════════════════

def test_feed_accumulates_across_batches():
    """分 3 批喂入，跨 batch 累积，第 3 批后到齐"""
    t = Chart4Transformer()

    r1 = t.feed(_ALL_REFS[:4])   # 第 1 批
    assert r1 is None

    r2 = t.feed(_ALL_REFS[4:8])  # 第 2 批
    assert r2 is None

    r3 = t.feed(_ALL_REFS[8:])   # 第 3 批 — 应该齐了
    assert r3 is not None
    assert len(r3.line_data) == 10
