"""
ws_manager.py — WebSocket 连接管理器

这个模块负责管理所有浏览器的 WebSocket 连接。

🔧 写给嵌入式开发者的类比：

想象一个"广播站"：
  - 每个打开大屏页面的浏览器 → 一台收音机（WebSocket 连接）
  - 这个管理器 → 广播站的控制台
  - connect() → 一台新的收音机开机、调到本站频率
  - broadcast() → 广播站对着所有收音机发一条消息
  - disconnect() → 收音机关机

为什么需要管理器而不是直接发消息？
  因为可能有多个用户同时打开大屏（多台设备）。
  管理器让我们一次性向所有连接的设备发送相同的数据。

WebSocket 和普通 HTTP 的区别：
  HTTP  = 寄信（我发一封，你收一封，然后断开）
  WebSocket = 打电话（接通后双方可以随时说话，直到挂断）
  TCP    = 电话线路本身（最底层的通信管道）
"""

from fastapi import WebSocket
import logging

# 🔧 Python 的 logging 模块 = 前端的 console.log
# 但是更灵活：可以控制日志级别、输出到文件等
logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    WebSocket 连接管理器

    负责：
    1. 记录所有活跃的 WebSocket 连接
    2. 向所有连接广播消息
    3. 处理连接断开后的清理工作
    """

    def __init__(self):
        """
        初始化管理器

        🔧 set() 是什么？
        Python 的 set（集合）类似 JavaScript 的 Set。
        和 list 的区别：set 中的元素不能重复，而且添加/删除的速度更快。
        这里不需要顺序，所以用 set 更合适。
        """
        # 存储所有活跃的 WebSocket 连接
        # 每条连接是一个 WebSocket 对象
        self._connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket) -> None:
        """
        接受一个新的 WebSocket 连接

        当浏览器打开页面、建立 WebSocket 连接时，FastAPI 会调用这个函数。

        参数:
            websocket: FastAPI 提供的 WebSocket 对象，代表这一条连接

        流程:
            1. 接受连接（websocket.accept() — 类似"接起电话"）
            2. 把这条连接加入管理器（告诉广播站"有新的收音机了"）
        """
        # 🔧 await websocket.accept()
        # WebSocket 握手过程：客户端说"你好，我想连"，服务端说"好的，请进"
        # 不接受的话，连接就处于"拨号中"状态，不能收发消息
        await websocket.accept()

        self._connections.add(websocket)
        logger.info(f"🔗 WebSocket 有新连接接入，当前连接数: {len(self._connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """
        断开一个 WebSocket 连接

        当浏览器关闭页面或网络断开时调用。
        """
        # 🔧 discard() vs remove():
        # discard() 如果元素不存在也不会报错（类似前端 optional chaining 的安全写法）
        # remove() 如果元素不存在会抛异常
        self._connections.discard(websocket)
        logger.info(f"🔌 WebSocket 连接断开，当前连接数: {len(self._connections)}")

    async def broadcast(self, data: dict) -> None:
        """
        向所有已连接的 WebSocket 客户端广播消息

        这是"推送数据"的核心方法。
        当 TCP Server 收到上位机报文后，调用此方法向所有浏览器发送更新。

        参数:
            data: 要发送的数据字典，会被自动转成 JSON 字符串

        注意事项:
            - 如果某个客户端已经断开但没有被清理，
              send_json() 会失败，我们捕获异常并清理它
        """
        logger.info(f"📡 广播消息到 {len(self._connections)} 个连接")

        # 🔧 list() 复制一份连接列表
        # 为什么？因为遍历过程中可能有连接断开（disconnect 修改了 set），
        # 直接遍历原集合会报错（类似 JavaScript 的数组在遍历时被修改）
        for connection in list(self._connections):
            try:
                # 🔧 send_json() 自动把 Python dict 转成 JSON 字符串发送
                # 前端收到的是 JavaScript 对象（JSON.parse 是自动的）
                await connection.send_json(data)
            except Exception:
                # 发送失败（例如客户端突然断网），从管理器中移除
                logger.warning("⚠️ 向某个客户端发送消息失败，将其移除")
                await self.disconnect(connection)

    @property
    def connection_count(self) -> int:
        """
        当前活跃连接数

        🔧 @property 是什么？
        Python 的 @property 装饰器让方法可以像属性一样访问。
        即：manager.connection_count 而不是 manager.connection_count()
        类似 JavaScript 的 getter。
        """
        return len(self._connections)


# ============================================================================
# 全局单例
# 整个应用只需要一个 ConnectionManager 实例
# 类似前端的 "export const wsManager = new ConnectionManager()"
# ============================================================================
manager = ConnectionManager()
