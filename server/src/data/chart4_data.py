"""
chart4_data.py — Chart4 数据的"内存数据库"

因为还没有真正的数据库（MySQL/PostgreSQL），我们先把数据存在 Python 的变量里。
你可以把它理解成：
    - 一张"便签纸" —— 程序启动时写上默认数据，运行时可以擦掉重写
    - 程序关闭后便签纸就丢了（数据不持久化）

🔧 后续如果要接真正的数据库：
   只需要改这个文件的 get_current_data() 和 update_data() 两个函数，
   让它们从数据库读写数据，其他文件的代码无需修改。
   这叫做"封装"——把变化关在一个地方。

线程安全说明：
   因为 TCP Server 和 WebSocket Server 可能同时访问这个数据
   （一个在写、一个在读），所以用 asyncio.Lock 保护。
   类比：前端的 useRef 配合 flag 防止并发写入。
"""

import asyncio

# ============================================================================
# 默认数据 — 与当前前端 chart4.tsx 中的硬编码值保持一致
# ============================================================================

# 这个字典就是我们的"便签纸"
# 用 Python 字典（dict）存储，类似 JavaScript 的 object 或 Map
_current_data: dict = {
    "line_data": [270, 400, 380, 420, 300, 410, 400, 330, 210, 290],
    "total_revenue": 99608,   # 收益总计（亿元）
    "enterprise_count": 7792,  # 企业数量（个）
}

# 🔧 asyncio.Lock 是什么？
# 想象你和同事共用一张便签纸：
#   - 如果你在写的时候，同事也在写 → 便签纸上的内容会乱掉
#   - Lock 就是一把"锁"：拿到锁的人才能操作便签纸，其他人排队等
#   - 这在前端也有类似概念：useRef 配合 flag 防止竞态条件
_lock = asyncio.Lock()


async def get_current_data() -> dict:
    """
    获取当前 Chart4 数据（读操作，加锁保护）

    返回:
        dict: 包含 line_data, total_revenue, enterprise_count 的字典

    为什么要 async？
        因为 Lock 的 acquire 操作是异步的——如果别人正在写，
        这个函数会等待（不阻塞整个程序），等别人写完再继续读。
    """
    # 🔧 async with = 获取锁 → 执行代码 → 自动释放锁
    # 类似前端的 try { lock() } finally { unlock() } 但更简洁
    async with _lock:
        # 返回一个副本（dict.copy()），防止外部修改影响内部数据
        return _current_data.copy()


async def update_data(new_data: dict) -> None:
    """
    更新 Chart4 数据（写操作，加锁保护）

    参数:
        new_data: 包含要更新的字段。可以只传部分字段（部分更新）。
                 例如只更新 total_revenue，不传 line_data 也行。

    调用方:
        - TCP Server 收到上位机报文后调用此函数
    """
    async with _lock:
        # 🔧 update() 方法：把 new_data 中的键值对"合并"到 _current_data 中
        # 类似 JavaScript 的 Object.assign(_current_data, new_data)
        _current_data.update(new_data)
