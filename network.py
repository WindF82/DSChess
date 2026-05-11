# 双步象棋 - 局域网联机模块 (房间码匹配)

import socket
import json
import threading
import time
from constants import DEFAULT_PORT, BUFFER_SIZE

DISCOVERY_PORT = DEFAULT_PORT + 1  # UDP广播端口
BROADCAST_INTERVAL = 1.5           # 广播间隔(秒)


class NetworkManager:
    def __init__(self, callback):
        self.callback = callback
        self.tcp_socket = None
        self.client_socket = None
        self.is_host = False
        self.connected = False
        self.running = False
        self.thread = None
        self.room_code = ""
        self.udp_socket = None
        self.udp_thread = None

    def start_host(self, room_code, port=DEFAULT_PORT):
        """作为主机启动: TCP服务器 + UDP广播房间码"""
        self.is_host = True
        self.room_code = room_code
        self.running = True

        # TCP服务器
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.tcp_socket.bind(("0.0.0.0", port))
        except OSError:
            self.callback("error", {"message": "端口被占用, 请稍后重试"})
            return False
        self.tcp_socket.listen(1)
        self.tcp_socket.settimeout(1.0)

        # 启动TCP接受线程
        self.thread = threading.Thread(target=self._host_accept, daemon=True)
        self.thread.start()

        # 启动UDP广播线程
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
        self.udp_thread.start()

        return True

    def _broadcast_loop(self):
        """定时广播房间码 (同时发往广播地址和本地回环，兼容同机/局域网)"""
        while self.running and not self.connected:
            try:
                msg = json.dumps({
                    "type": "room_announce",
                    "code": self.room_code,
                    "port": DEFAULT_PORT,
                }).encode("utf-8")
                for target in ("255.255.255.255", "127.0.0.1"):
                    try:
                        self.udp_socket.sendto(msg, (target, DISCOVERY_PORT))
                    except OSError:
                        pass
            except OSError:
                pass
            time.sleep(BROADCAST_INTERVAL)

    def _host_accept(self):
        """主机等待客户端连接"""
        while self.running:
            try:
                self.client_socket, addr = self.tcp_socket.accept()
                self.client_socket.settimeout(0.5)
                self.connected = True
                self._start_receive()
                self.callback("connected", {"addr": str(addr)})
                break
            except socket.timeout:
                continue
            except OSError:
                break

    def join_room(self, room_code, timeout=15):
        """作为客户端: UDP监听 → 匹配房间码 → TCP连接"""
        self.is_host = False
        self.room_code = room_code
        self.running = True

        # 创建UDP监听
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.udp_socket.bind(("0.0.0.0", DISCOVERY_PORT))
        except OSError:
            self.udp_socket.bind(("0.0.0.0", 0))
        self.udp_socket.settimeout(2.0)

        # 监听房间广播
        host_ip = self._listen_for_room(room_code, timeout)
        # 回退: 若广播未找到, 尝试直接连接本机 (同机/防火墙场景)
        if host_ip is None:
            host_ip = self._try_localhost(room_code)
        if host_ip is None:
            self.callback("error", {"message": f"未找到房间码 '{room_code}', 请确认房间码或局域网连接"})
            return False

        # 连接到主机
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(5.0)
        try:
            self.tcp_socket.connect((host_ip, DEFAULT_PORT))
            self.client_socket = self.tcp_socket
            self.connected = True
            self.client_socket.settimeout(0.5)
            self._start_receive()
            self.callback("connected", {"addr": host_ip})
            return True
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self.callback("error", {"message": f"连接失败: {e}"})
            return False

    def _listen_for_room(self, room_code, timeout):
        """监听UDP广播, 匹配房间码后返回主机IP"""
        deadline = time.time() + timeout
        while time.time() < deadline and self.running:
            try:
                data, addr = self.udp_socket.recvfrom(BUFFER_SIZE)
                msg = json.loads(data.decode("utf-8"))
                if msg.get("type") == "room_announce" and msg.get("code") == room_code:
                    return addr[0]
            except socket.timeout:
                continue
            except (OSError, json.JSONDecodeError):
                continue
        return None

    def _try_localhost(self, room_code, timeout=1.0):
        """回退: 尝试直接连接本机TCP (绕过UDP广播被屏蔽的场景)"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect(("127.0.0.1", DEFAULT_PORT))
            sock.close()
            return "127.0.0.1"
        except (socket.timeout, ConnectionRefusedError, OSError):
            return None

    def connect_to_host(self, host, port=DEFAULT_PORT):
        """(保留) 直接通过IP连接"""
        self.is_host = False
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.settimeout(5.0)
        try:
            self.tcp_socket.connect((host, port))
            self.client_socket = self.tcp_socket
            self.connected = True
            self.client_socket.settimeout(0.5)
            self.running = True
            self._start_receive()
            self.callback("connected", {"addr": host})
            return True
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self.callback("error", {"message": f"连接失败: {e}"})
            return False

    def _start_receive(self):
        self.recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.recv_thread.start()

    def _receive_loop(self):
        while self.running and self.connected:
            try:
                data = self.client_socket.recv(BUFFER_SIZE)
                if not data:
                    self.connected = False
                    self.callback("disconnected", {})
                    break
                msg = json.loads(data.decode("utf-8"))
                self.callback(msg.get("type", "unknown"), msg.get("data", {}))
            except socket.timeout:
                continue
            except (ConnectionResetError, ConnectionAbortedError, OSError, json.JSONDecodeError):
                self.connected = False
                self.callback("disconnected", {})
                break

    def send(self, msg_type, data=None):
        if not self.connected or not self.client_socket:
            return False
        try:
            msg = json.dumps({"type": msg_type, "data": data or {}})
            self.client_socket.sendall(msg.encode("utf-8"))
            return True
        except OSError:
            self.connected = False
            self.callback("disconnected", {})
            return False

    def stop(self):
        self.running = False
        if self.udp_socket:
            try:
                self.udp_socket.close()
            except OSError:
                pass
        if self.client_socket:
            try:
                self.client_socket.close()
            except OSError:
                pass
        if self.tcp_socket:
            try:
                self.tcp_socket.close()
            except OSError:
                pass
        self.connected = False

    def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "127.0.0.1"
