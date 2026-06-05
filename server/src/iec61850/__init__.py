"""
iec61850/ — IEC 61850 变电站自动化协议支持

当前阶段（本地仿真）：
  - config.py — 定义需采集的 DO ref 及其默认值

后续真实网关接入时，本目录将扩展：
  - scl_parser.py  — SCL 配置文件解析
  - data_model.py  — 逻辑节点 / 数据对象的 Python 类型映射
  - connection.py  — MMS 连接管理（或网关连接配置）

注意：IEC 61850 协议解析（ASN.1/BER 解码、MMS 封帧）在 C 网关侧完成，
      Python 后端不直接处理原始 IEC 61850 二进制报文。
"""

from src.iec61850.config import DATA_POINT_DEFS

__all__ = ["DATA_POINT_DEFS"]
