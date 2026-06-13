"""
server/tests/ — 测试和模拟器

目录结构:
  test_engine.py              单元测试 — DataEngine 核心逻辑
  test_config_loader.py       单元测试 — 配置加载与过滤
  test_chart4_transformer.py  单元测试 — IEC 61850 数据转换

  test_iec61850_gateway.py    集成测试 — 模拟 IEC 61850 网关发原始数据对象

运行方式:
  python -m pytest tests/ -v                              # 全部
  python -m pytest tests/ -v -k "test_engine"             # 只跑引擎
  python -m pytest tests/ -v --ignore=tests/test_iec61850_gateway.py
                                                          # 只跑单元（跳过集成）
"""
