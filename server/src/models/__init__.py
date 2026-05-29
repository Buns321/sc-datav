"""
server/src/models/ — 数据模型层

这个目录下的文件用 Pydantic 定义数据的"格式"（类似 TypeScript 的 interface）。
每一份从网络收到的 JSON 数据，都要经过这些模型校验，确保格式正确。

类比：
    TypeScript 的 type/interface 定义 → 编译时类型检查
    Pydantic 的 BaseModel 定义 → 运行时数据校验
"""
