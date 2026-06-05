"""
config.py — IEC 61850 数据对象引用 (DO ref) 定义清单

数据来源: server/config/mapping.yaml
         如果 YAML 不可用，降级到 config_loader 内置默认值。

对下游的契约：
  - 导出 DATA_POINT_DEFS: list[DataPointDef] — 仿真器、transformer 共同引用
  - 导出 DataPointDef 类型 — 保证类型一致
"""

from src.config_loader import load_data_points, DataPointDef

# 下游统一使用 DATA_POINT_DEFS，内部来自 YAML 或 fallback
DATA_POINT_DEFS: list[DataPointDef] = load_data_points()
