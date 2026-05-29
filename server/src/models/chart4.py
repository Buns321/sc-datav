"""
chart4.py — Chart4（企业收益统计）的数据格式定义

这个文件用 Pydantic 定义 Chart4 接收和发送的数据"应该长什么样"。

🔧 写给嵌入式开发者：

类比：
   TypeScript 的 interface → 编译时帮你检查类型，编译后消失
   Pydantic 的 BaseModel → 运行时帮你检查数据，数据不对就直接报错

比如你定义一个字段是 int（整数），如果收到的 JSON 里这个字段是字符串 "123"，
Pydantic 会尝试自动转换（"123" → 123），如果转换不了就报错。
这比手动写一堆 if/else 检查数据要简洁得多。

当前 Chart4 展示的内容（对应前端 chart4.tsx）：
  1. 折线图：10 个数据点
  2. 收益总计数字卡片
  3. 企业数量数字卡片
"""

from pydantic import BaseModel, Field


class Chart4Payload(BaseModel):
    """
    Chart4 的数据内容（payload 字段的内容）

    这是 TCP 报文和 WebSocket 消息共用的数据格式。
    前端拿到这份数据后直接填入 ECharts 配置中。
    """

    # 🔧 Field(description="...") 的作用：
    # 不仅给人类看，FastAPI 还会用它自动生成 API 文档（/docs 页面）
    line_data: list[int] = Field(
        default_factory=lambda: [270, 400, 380, 420, 300, 410, 400, 330, 210, 290],
        description="折线图的 10 个数据点（对应图表的 Y 轴值）",
    )

    total_revenue: int = Field(
        default=99608,
        description="收益总计，单位：亿元",
        ge=0,  # 🔧 ge=0 意思是 greater or equal to 0，即"必须 ≥ 0"
    )

    enterprise_count: int = Field(
        default=7792,
        description="企业总数，单位：个",
        ge=0,
    )


class Chart4Message(BaseModel):
    """
    Chart4 的完整报文格式

    这是上位机模拟器通过 TCP 发送的 JSON 报文结构，
    也是后端通过 WebSocket 推送给前端的数据结构。
    """

    type: str = Field(
        default="chart4_update",
        description="消息类型。前端根据这个字段判断数据属于哪个频道",
        # 🔧 虽然目前只有 chart4，但保留 type 字段是为了
        # 后续扩展（chart1, chart2, ...）时不需要改消息结构
    )

    timestamp: str = Field(
        default="",
        description="报文发送时间，ISO 8601 格式（如 2026-05-28T12:00:00Z）",
    )

    payload: Chart4Payload = Field(
        default_factory=Chart4Payload,
        description="Chart4 的实际业务数据",
    )
