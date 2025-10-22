"""Transport Layer for SAFE Agent Communication

This module provides various transport implementations for agent communication.
"""

import asyncio
import json
import logging
import socket
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from .protocols import MessageEnvelope, TransportType, CommunicationProtocol


class BaseTransport(ABC):
    """传输层基类"""

    def __init__(self, transport_type: TransportType):
        """初始化传输层

        Args:
            transport_type: 传输类型
        """
        self.transport_type = transport_type
        self.connected = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    @abstractmethod
    async def connect(self, **kwargs) -> bool:
        """连接传输层

        Args:
            **kwargs: 连接参数

        Returns:
            是否连接成功
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开连接

        Returns:
            是否断开成功
        """
        pass

    @abstractmethod
    async def send(self, envelope: MessageEnvelope) -> bool:
        """发送消息

        Args:
            envelope: 消息信封

        Returns:
            是否发送成功
        """
        pass

    @abstractmethod
    async def receive(self) -> Optional[MessageEnvelope]:
        """接收消息

        Returns:
            消息信封或None
        """
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """检查是否已连接

        Returns:
            是否已连接
        """
        pass


class MemoryTransport(BaseTransport):
    """内存传输实现"""

    def __init__(self):
        """初始化内存传输"""
        super().__init__(TransportType.IN_MEMORY)
        self.message_queue = asyncio.Queue()
        self.handlers: Dict[str, Callable] = {}

    async def connect(self, **kwargs) -> bool:
        """连接（内存传输不需要真正连接）"""
        self.connected = True
        self.logger.info("Memory transport connected")
        return True

    async def disconnect(self) -> bool:
        """断开连接"""
        self.connected = False
        self.logger.info("Memory transport disconnected")
        return True

    async def send(self, envelope: MessageEnvelope) -> bool:
        """发送消息到内存队列"""
        if not self.connected:
            return False

        try:
            # 直接处理消息
            handler = self.handlers.get(envelope.destination)
            if handler:
                await handler(envelope)
                return True
            else:
                # 如果没有处理器，放入队列
                await self.message_queue.put(envelope)
                return True

        except Exception as e:
            self.logger.error(f"Failed to send message via memory transport: {e}")
            return False

    async def receive(self) -> Optional[MessageEnvelope]:
        """从内存队列接收消息"""
        if not self.connected:
            return None

        try:
            # 非阻塞接收
            return await asyncio.wait_for(self.message_queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Failed to receive message via memory transport: {e}")
            return None

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

    def register_handler(self, destination: str, handler: Callable) -> None:
        """注册消息处理器"""
        self.handlers[destination] = handler

    def unregister_handler(self, destination: str) -> None:
        """注销消息处理器"""
        if destination in self.handlers:
            del self.handlers[destination]


class HTTPTransport(BaseTransport):
    """HTTP传输实现"""

    def __init__(self):
        """初始化HTTP传输"""
        super().__init__(TransportType.HTTP)
        self.base_url = ""
        self.session = None
        self.server_port = None
        self.server_task = None

    async def connect(self, base_url: str = "", server_port: int = 8080, **kwargs) -> bool:
        """连接HTTP传输

        Args:
            base_url: 基础URL
            server_port: 服务器端口
            **kwargs: 其他参数

        Returns:
            是否连接成功
        """
        try:
            self.base_url = base_url
            self.server_port = server_port

            # 创建HTTP客户端会话
            import aiohttp
            self.session = aiohttp.ClientSession()

            # 启动HTTP服务器
            self.server_task = asyncio.create_task(self._start_server())

            self.connected = True
            self.logger.info(f"HTTP transport connected on port {server_port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect HTTP transport: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开HTTP连接"""
        try:
            self.connected = False

            # 停止服务器
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass

            # 关闭客户端会话
            if self.session:
                await self.session.close()

            self.logger.info("HTTP transport disconnected")
            return True

        except Exception as e:
            self.logger.error(f"Failed to disconnect HTTP transport: {e}")
            return False

    async def send(self, envelope: MessageEnvelope) -> bool:
        """通过HTTP发送消息"""
        if not self.connected or not self.session:
            return False

        try:
            url = f"{envelope.destination}/message"
            data = envelope.to_dict()

            async with self.session.post(url, json=data, timeout=10) as response:
                if response.status == 200:
                    return True
                else:
                    self.logger.error(f"HTTP send failed with status {response.status}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to send message via HTTP transport: {e}")
            return False

    async def receive(self) -> Optional[MessageEnvelope]:
        """HTTP传输不使用主动接收模式，通过服务器接收"""
        return None

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

    async def _start_server(self) -> None:
        """启动HTTP服务器"""
        try:
            from aiohttp import web

            async def handle_message(request):
                """处理接收到的消息"""
                try:
                    data = await request.json()
                    envelope = MessageEnvelope.from_dict(data)

                    # 这里应该调用消息处理器
                    # handler = self.handlers.get(envelope.destination)
                    # if handler:
                    #     await handler(envelope)

                    return web.json_response({"status": "received"})
                except Exception as e:
                    return web.json_response({"error": str(e)}, status=400)

            app = web.Application()
            app.router.add_post('/message', handle_message)

            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, 'localhost', self.server_port)
            await site.start()

            self.logger.info(f"HTTP server started on port {self.server_port}")

            # 保持服务器运行
            while self.connected:
                await asyncio.sleep(1)

        except Exception as e:
            self.logger.error(f"HTTP server error: {e}")


class WebSocketTransport(BaseTransport):
    """WebSocket传输实现"""

    def __init__(self):
        """初始化WebSocket传输"""
        super().__init__(TransportType.WEBSOCKET)
        self.connections: Dict[str, Any] = {}  # agent_id -> websocket
        self.server_port = None
        self.server_task = None
        self.handlers: Dict[str, Callable] = {}

    async def connect(self, server_port: int = 8081, **kwargs) -> bool:
        """连接WebSocket传输

        Args:
            server_port: 服务器端口
            **kwargs: 其他参数

        Returns:
            是否连接成功
        """
        try:
            self.server_port = server_port

            # 启动WebSocket服务器
            self.server_task = asyncio.create_task(self._start_server())

            self.connected = True
            self.logger.info(f"WebSocket transport connected on port {server_port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect WebSocket transport: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开WebSocket连接"""
        try:
            self.connected = False

            # 关闭所有连接
            for ws in self.connections.values():
                try:
                    await ws.close()
                except Exception:
                    pass
            self.connections.clear()

            # 停止服务器
            if self.server_task:
                self.server_task.cancel()
                try:
                    await self.server_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("WebSocket transport disconnected")
            return True

        except Exception as e:
            self.logger.error(f"Failed to disconnect WebSocket transport: {e}")
            return False

    async def send(self, envelope: MessageEnvelope) -> bool:
        """通过WebSocket发送消息"""
        if not self.connected:
            return False

        try:
            ws = self.connections.get(envelope.destination)
            if not ws:
                self.logger.error(f"No WebSocket connection for {envelope.destination}")
                return False

            data = envelope.to_dict()
            await ws.send_text(json.dumps(data))
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message via WebSocket transport: {e}")
            return False

    async def receive(self) -> Optional[MessageEnvelope]:
        """WebSocket传输不使用主动接收模式"""
        return None

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

    async def _start_server(self) -> None:
        """启动WebSocket服务器"""
        try:
            import websockets

            async def handle_connection(websocket, path):
                """处理WebSocket连接"""
                try:
                    # 等待认证消息
                    auth_message = await websocket.recv()
                    auth_data = json.loads(auth_message)
                    agent_id = auth_data.get("agent_id")

                    if not agent_id:
                        await websocket.close(1008, "Agent ID required")
                        return

                    # 注册连接
                    self.connections[agent_id] = websocket
                    self.logger.info(f"WebSocket connection established for {agent_id}")

                    # 处理消息
                    try:
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                envelope = MessageEnvelope.from_dict(data)

                                # 调用处理器
                                handler = self.handlers.get(envelope.destination)
                                if handler:
                                    await handler(envelope)

                            except Exception as e:
                                self.logger.error(f"Error processing WebSocket message: {e}")

                    except websockets.exceptions.ConnectionClosed:
                        pass
                    finally:
                        # 清理连接
                        if agent_id in self.connections:
                            del self.connections[agent_id]
                        self.logger.info(f"WebSocket connection closed for {agent_id}")

                except Exception as e:
                    self.logger.error(f"WebSocket connection error: {e}")

            # 启动服务器
            server = await websockets.serve(handle_connection, "localhost", self.server_port)
            self.logger.info(f"WebSocket server started on port {self.server_port}")

            # 保持服务器运行
            while self.connected:
                await asyncio.sleep(1)

            await server.close()

        except Exception as e:
            self.logger.error(f"WebSocket server error: {e}")

    def register_handler(self, destination: str, handler: Callable) -> None:
        """注册消息处理器"""
        self.handlers[destination] = handler


class RedisTransport(BaseTransport):
    """Redis传输实现"""

    def __init__(self):
        """初始化Redis传输"""
        super().__init__(TransportType.REDIS)
        self.redis_client = None
        self.pubsub = None
        self.listener_task = None
        self.handlers: Dict[str, Callable] = {}

    async def connect(self, host: str = "localhost", port: int = 6379, db: int = 0, **kwargs) -> bool:
        """连接Redis

        Args:
            host: Redis主机
            port: Redis端口
            db: Redis数据库
            **kwargs: 其他参数

        Returns:
            是否连接成功
        """
        try:
            import redis.asyncio as redis

            # 创建Redis客户端
            self.redis_client = redis.Redis(host=host, port=port, db=db, **kwargs)

            # 测试连接
            await self.redis_client.ping()

            # 创建发布订阅客户端
            self.pubsub = self.redis_client.pubsub()

            # 启动监听任务
            self.listener_task = asyncio.create_task(self._listen_messages())

            self.connected = True
            self.logger.info(f"Redis transport connected to {host}:{port}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect Redis transport: {e}")
            return False

    async def disconnect(self) -> bool:
        """断开Redis连接"""
        try:
            self.connected = False

            # 停止监听任务
            if self.listener_task:
                self.listener_task.cancel()
                try:
                    await self.listener_task
                except asyncio.CancelledError:
                    pass

            # 关闭发布订阅
            if self.pubsub:
                await self.pubsub.close()

            # 关闭Redis客户端
            if self.redis_client:
                await self.redis_client.close()

            self.logger.info("Redis transport disconnected")
            return True

        except Exception as e:
            self.logger.error(f"Failed to disconnect Redis transport: {e}")
            return False

    async def send(self, envelope: MessageEnvelope) -> bool:
        """通过Redis发送消息"""
        if not self.connected or not self.redis_client:
            return False

        try:
            data = envelope.to_dict()
            channel = f"agent:{envelope.destination}"
            await self.redis_client.publish(channel, json.dumps(data))
            return True

        except Exception as e:
            self.logger.error(f"Failed to send message via Redis transport: {e}")
            return False

    async def receive(self) -> Optional[MessageEnvelope]:
        """Redis传输不使用主动接收模式"""
        return None

    def is_connected(self) -> bool:
        """检查连接状态"""
        return self.connected

    async def _listen_messages(self) -> None:
        """监听Redis消息"""
        try:
            # 订阅所有Agent频道
            await self.pubsub.psubscribe("agent:*")

            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    try:
                        data = json.loads(message["data"])
                        envelope = MessageEnvelope.from_dict(data)

                        # 调用处理器
                        handler = self.handlers.get(envelope.destination)
                        if handler:
                            await handler(envelope)

                    except Exception as e:
                        self.logger.error(f"Error processing Redis message: {e}")

        except Exception as e:
            self.logger.error(f"Redis listener error: {e}")

    def register_handler(self, destination: str, handler: Callable) -> None:
        """注册消息处理器"""
        self.handlers[destination] = handler


class TransportManager:
    """传输管理器"""

    def __init__(self):
        """初始化传输管理器"""
        self.transports: Dict[TransportType, BaseTransport] = {}
        self.active_transport: Optional[BaseTransport] = None
        self.logger = logging.getLogger("TransportManager")

    def register_transport(self, transport: BaseTransport) -> None:
        """注册传输层

        Args:
            transport: 传输层实例
        """
        self.transports[transport.transport_type] = transport
        self.logger.info(f"Registered transport: {transport.transport_type.value}")

    def set_active_transport(self, transport_type: TransportType) -> bool:
        """设置活动传输层

        Args:
            transport_type: 传输类型

        Returns:
           是否设置成功
        """
        transport = self.transports.get(transport_type)
        if transport:
            self.active_transport = transport
            self.logger.info(f"Active transport set to: {transport_type.value}")
            return True
        else:
            self.logger.error(f"Transport not registered: {transport_type.value}")
            return False

    async def connect_transport(self, transport_type: TransportType, **kwargs) -> bool:
        """连接特定传输层

        Args:
            transport_type: 传输类型
            **kwargs: 连接参数

        Returns:
            是否连接成功
        """
        transport = self.transports.get(transport_type)
        if transport:
            return await transport.connect(**kwargs)
        else:
            self.logger.error(f"Transport not registered: {transport_type.value}")
            return False

    async def disconnect_transport(self, transport_type: TransportType) -> bool:
        """断开特定传输层

        Args:
            transport_type: 传输类型

        Returns:
            是否断开成功
        """
        transport = self.transports.get(transport_type)
        if transport:
            return await transport.disconnect()
        else:
            self.logger.error(f"Transport not registered: {transport_type.value}")
            return False

    async def send_message(self, envelope: MessageEnvelope) -> bool:
        """通过活动传输层发送消息

        Args:
            envelope: 消息信封

        Returns:
            是否发送成功
        """
        if not self.active_transport:
            self.logger.error("No active transport")
            return False

        return await self.active_transport.send(envelope)

    def get_transport_stats(self) -> Dict[str, Any]:
        """获取传输层统计信息

        Returns:
            统计信息
        """
        return {
            "total_transports": len(self.transports),
            "active_transport": self.active_transport.transport_type.value if self.active_transport else None,
            "registered_transports": [t.value for t in self.transports.keys()],
            "connection_status": {
                t.value: transport.is_connected()
                for t, transport in self.transports.items()
            }
        }


# 创建默认的传输管理器
default_transport_manager = TransportManager()
default_transport_manager.register_transport(MemoryTransport())