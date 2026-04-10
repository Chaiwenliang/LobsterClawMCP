"""
LobsterClaw MCP - 带 API Key 认证的 SSE 网络服务器
基于原始 lobster_claw_mcp.py，增加 API Key 中间件认证

使用方法:
    1. 设置环境变量:
       export LOBSTER_API_KEY="your-secret-key"

    2. 启动服务器:
       python3 server_with_auth.py --host 0.0.0.0 --port 8090

    3. 客户端连接时携带 API Key:
       Header: Authorization: Bearer your-secret-key
       或 URL 参数: ?api_key=your-secret-key
"""

import argparse
import logging
import os
import random
import subprocess
import time
from logging.handlers import RotatingFileHandler
from uuid import uuid4

import pyautogui
import uvicorn
from PIL import ImageGrab
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

try:
    from fastmcp import FastMCP
except Exception:
    from mcp.server.fastmcp import FastMCP

try:
    from mcp.server.sse import SseServerTransport
except Exception:
    from mcp.sse import SseServerTransport

# ==================== 日志配置 ====================
log_path = os.path.expanduser("~/lobster_claw.log")
logger = logging.getLogger("LobsterClaw")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(
        log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter(
        "[%(asctime)s] [%(trace_id)s] %(levelname)s %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

_old_factory = logging.getLogRecordFactory()


def _record_factory(*args, **kwargs):
    rec = _old_factory(*args, **kwargs)
    if not hasattr(rec, "trace_id"):
        rec.trace_id = "--------"
    return rec


logging.setLogRecordFactory(_record_factory)


class TraceLog:
    def __enter__(self):
        self.tid = str(uuid4())[:8]
        self.old = logging.getLogRecordFactory()

        def factory(*args, **kwargs):
            rec = self.old(*args, **kwargs)
            rec.trace_id = self.tid
            return rec

        logging.setLogRecordFactory(factory)
        return self

    def __exit__(self, *args):
        logging.setLogRecordFactory(self.old)


def log_info(msg):
    logger.info(msg)


def log_error(msg):
    logger.error(msg)


# ==================== 配置常量 ====================
pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = True

BASE_INTERVAL = 0.12
TYPE_JITTER = 0.08
MOVE_MIN = 0.3
MOVE_MAX = 0.8
CLICK_OFFSET = 5
AFTER_CLICK = 0.7

# ==================== API Key 认证中间件 ====================
API_KEY = os.environ.get("LOBSTER_API_KEY", "")

# 不需要认证的路径
EXEMPT_PATHS = {"/health"}


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """API Key Bearer Token 认证中间件"""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # 健康检查等路径免认证
        if path in EXEMPT_PATHS:
            return await call_next(request)

        # SSE 连接路径也需要认证
        # 检查 Authorization header: Bearer <API_KEY>
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # 去掉 "Bearer " 前缀
            if token == API_KEY:
                return await call_next(request)

        # 检查 URL 查询参数: ?api_key=<API_KEY>
        query_key = request.query_params.get("api_key", "")
        if query_key == API_KEY:
            return await call_next(request)

        # 认证失败
        return JSONResponse(
            status_code=401,
            content={"error": "未授权：请提供有效的 API Key", "status": "unauthorized"},
        )


# ==================== MCP 工具定义 ====================
mcp = FastMCP(name="LobsterClaw")


@mcp.tool()
def screenshot() -> str:
    try:
        img = ImageGrab.grab()
        path = os.path.expanduser("~/screen_latest.png")
        img.save(path, "PNG")
        log_info("screenshot: 保存成功")
        return "✅ 已截图"
    except Exception as e:
        log_error(f"screenshot 失败: {str(e)}")
        return "❌ 截图失败"


@mcp.tool()
def mouse_move(x: int, y: int) -> str:
    try:
        rx = x + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        ry = y + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        dur = random.uniform(MOVE_MIN, MOVE_MAX)
        pyautogui.moveTo(rx, ry, duration=dur, tween=pyautogui.easeOutQuad)
        time.sleep(random.uniform(0.1, 0.2))
        log_info(f"mouse_move: ({rx},{ry})")
        return f"✅ 已移动到 ({rx},{ry})"
    except Exception as e:
        log_error(f"mouse_move 失败: {e}")
        return "❌ 移动失败"


@mcp.tool()
def click(x: int, y: int) -> str:
    try:
        rx = x + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        ry = y + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        dur = random.uniform(MOVE_MIN, MOVE_MAX)
        pyautogui.moveTo(rx, ry, duration=dur, tween=pyautogui.easeOutQuad)
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.click()
        time.sleep(random.uniform(AFTER_CLICK * 0.8, AFTER_CLICK * 1.2))
        log_info(f"click: ({rx},{ry})")
        return f"✅ 已点击 ({rx},{ry})"
    except Exception as e:
        log_error(f"click 失败: {e}")
        return "❌ 点击失败"


@mcp.tool()
def right_click(x: int, y: int) -> str:
    try:
        rx = x + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        ry = y + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        dur = random.uniform(MOVE_MIN, MOVE_MAX)
        pyautogui.moveTo(rx, ry, duration=dur, tween=pyautogui.easeOutQuad)
        time.sleep(random.uniform(0.05, 0.15))
        pyautogui.rightClick()
        time.sleep(random.uniform(0.5, 0.9))
        log_info(f"right_click: ({rx},{ry})")
        return f"✅ 已右键 ({rx},{ry})"
    except Exception as e:
        log_error(f"right_click 失败: {e}")
        return "❌ 右键失败"


@mcp.tool()
def scroll(down: int = 3) -> str:
    try:
        pyautogui.scroll(-abs(down))
        time.sleep(random.uniform(0.2, 0.4))
        log_info(f"scroll: 向下{down}")
        return "✅ 已滚动"
    except Exception as e:
        log_error(f"scroll 失败: {e}")
        return "❌ 滚动失败"


@mcp.tool()
def type_slow(text: str) -> str:
    try:
        for c in text:
            iv = random.uniform(BASE_INTERVAL, BASE_INTERVAL + TYPE_JITTER)
            pyautogui.write(c, interval=iv)
        time.sleep(random.uniform(0.3, 0.7))
        log_info(f"type_slow: 长度{len(text)}")
        return "✅ 已输入文字"
    except Exception as e:
        log_error(f"type_slow 失败: {e}")
        return "❌ 输入失败"


@mcp.tool()
def hotkey(key: str) -> str:
    try:
        pyautogui.hotkey(*key.split("+"))
        time.sleep(random.uniform(0.4, 0.7))
        log_info(f"hotkey: {key}")
        return f"✅ 已按 {key}"
    except Exception as e:
        log_error(f"hotkey 失败 {key}: {e}")
        return "❌ 快捷键失败"


@mcp.tool()
def wait(sec: float = 1.0) -> str:
    try:
        s = max(0.2, min(5.0, sec))
        time.sleep(s)
        log_info(f"wait: {s:.1f}s")
        return f"✅ 已等待 {s:.1f}s"
    except Exception as e:
        log_error(f"wait 失败: {e}")
        return "❌ 等待失败"


@mcp.tool()
def open_app(app_name: str) -> str:
    try:
        subprocess.run(["open", "-a", app_name], capture_output=True)
        time.sleep(random.uniform(1.5, 3.0))
        log_info(f"open_app: {app_name}")
        return f"✅ 已打开 {app_name}"
    except Exception as e:
        log_error(f"open_app 失败 {app_name}: {e}")
        return "❌ 打开应用失败"


@mcp.tool()
def activate_app(app_name: str) -> str:
    try:
        script = f'tell application "{app_name}" to activate'
        subprocess.run(["osascript", "-e", script], capture_output=True)
        time.sleep(0.5)
        log_info(f"activate_app: {app_name}")
        return f"✅ 已激活 {app_name}"
    except Exception as e:
        log_error(f"activate_app 失败: {e}")
        return "❌ 激活窗口失败"


@mcp.tool()
def get_mouse_pos() -> str:
    try:
        pos = pyautogui.position()
        x, y = pos.x, pos.y
        log_info(f"get_mouse_pos: ({x},{y})")
        return f"✅ 当前坐标 ({x},{y})"
    except Exception as e:
        log_error(f"get_mouse_pos 失败: {e}")
        return "❌ 获取坐标失败"


@mcp.tool()
def fill_password(service: str, account: str) -> str:
    """
    安全地从 macOS 钥匙串中获取并自动输入密码。
    AI 不会看到明文密码。
    """
    try:
        res = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
        )
        pwd = res.stdout.strip()
        if not pwd:
            tip = f'❌ 找不到密码。请在终端运行: security add-generic-password -s "{service}" -a "{account}" -w "YOUR_PASSWORD"'
            log_error(f"fill_password 失败: 找不到 {service} 的密码")
            return tip
        for char in pwd:
            iv = random.uniform(BASE_INTERVAL, BASE_INTERVAL + TYPE_JITTER)
            pyautogui.write(char, interval=iv)
        log_info(f"fill_password 成功: 已填充 {service} 的密码")
        return "✅ 密码已安全填充"
    except Exception as e:
        log_error(f"fill_password 异常: {e}")
        return f"❌ 填充失败: {e}"


# ==================== 创建带认证的 SSE 应用 ====================
def create_authenticated_app(server, *, debug: bool = False) -> Starlette:
    """创建带 API Key 认证的 Starlette SSE 应用"""

    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
            request.scope, request.receive, request._send
        ) as (read_stream, write_stream):
            await server.run(
                read_stream, write_stream, server.create_initialization_options()
            )

    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "name": "LobsterClaw", "auth": "enabled"})

    # 创建带中间件的 Starlette 应用
    app = Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/health", endpoint=health),
            Mount("/messages/", app=sse.handle_post_message),
        ],
        middleware=[Middleware(APIKeyAuthMiddleware)],
    )

    return app


# ==================== 主入口 ====================
def main():
    parser = argparse.ArgumentParser(
        description="LobsterClaw MCP Server (带 API Key 认证)"
    )
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8090, help="监听端口 (默认: 8090)")
    args = parser.parse_args()

    # 检查 API Key
    if not API_KEY:
        print("⚠️  警告: 未设置 LOBSTER_API_KEY 环境变量！")
        print("   任何人都可以访问此服务器！")
        print("   建议设置: export LOBSTER_API_KEY='your-secret-key'")
        print()
        confirm = input("是否继续无认证启动？(y/N): ")
        if confirm.lower() != "y":
            print("已退出。请设置 API Key 后重试。")
            return

    # 获取 MCP server 对象
    mcp_server = getattr(mcp, "_mcp_server", None)
    if mcp_server is None:
        mcp_server = mcp

    # 创建带认证的应用
    app = create_authenticated_app(mcp_server, debug=False)

    print(f"🦞 LobsterClaw MCP Server")
    print(f"   地址: http://{args.host}:{args.port}")
    print(f"   SSE:  http://{args.host}:{args.port}/sse")
    print(f"   健康检查: http://{args.host}:{args.port}/health")
    print(f"   认证: {'✅ 已启用 (LOBSTER_API_KEY)' if API_KEY else '❌ 未启用'}")
    print()

    log_info(f"Starting authenticated SSE server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
