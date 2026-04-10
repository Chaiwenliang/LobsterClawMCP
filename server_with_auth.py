"""
LobsterClaw MCP - 带 API Key 认证的 SSE 网络服务器（修复版）
使用方法:
    export LOBSTER_API_KEY="your-secret-key"
    python3 server_with_auth.py --host 0.0.0.0 --port 8090
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

log_path = os.path.expanduser("~/lobster_claw.log")
logger = logging.getLogger("LobsterClaw")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    formatter = logging.Formatter("[%(asctime)s] [%(trace_id)s] %(levelname)s %(message)s")
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

pyautogui.PAUSE = 0.0
pyautogui.FAILSAFE = True
BASE_INTERVAL = 0.12
TYPE_JITTER = 0.08
MOVE_MIN = 0.3
MOVE_MAX = 0.8
CLICK_OFFSET = 5
AFTER_CLICK = 0.7

API_KEY = os.environ.get("LOBSTER_API_KEY", "")

def check_auth(request):
    if not API_KEY:
        return True
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer ") and auth[7:] == API_KEY:
        return True
    if request.query_params.get("api_key", "") == API_KEY:
        return True
    return False

mcp = FastMCP(name="LobsterClaw")

@mcp.tool()
def screenshot() -> str:
    try:
        img = ImageGrab.grab()
        path = os.path.expanduser("~/screen_latest.png")
        img.save(path, "PNG")
        log_info("screenshot: ok")
        return "ok screenshot saved"
    except Exception as e:
        log_error(f"screenshot failed: {e}")
        return f"screenshot failed: {e}"

@mcp.tool()
def mouse_move(x: int, y: int) -> str:
    try:
        rx = x + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        ry = y + random.randint(-CLICK_OFFSET, CLICK_OFFSET)
        dur = random.uniform(MOVE_MIN, MOVE_MAX)
        pyautogui.moveTo(rx, ry, duration=dur, tween=pyautogui.easeOutQuad)
        time.sleep(random.uniform(0.1, 0.2))
        log_info(f"mouse_move: ({rx},{ry})")
        return f"moved to ({rx},{ry})"
    except Exception as e:
        log_error(f"mouse_move failed: {e}")
        return f"mouse_move failed: {e}"

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
        return f"clicked ({rx},{ry})"
    except Exception as e:
        log_error(f"click failed: {e}")
        return f"click failed: {e}"

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
        return f"right clicked ({rx},{ry})"
    except Exception as e:
        log_error(f"right_click failed: {e}")
        return f"right_click failed: {e}"

@mcp.tool()
def scroll(down: int = 3) -> str:
    try:
        pyautogui.scroll(-abs(down))
        time.sleep(random.uniform(0.2, 0.4))
        log_info(f"scroll: down {down}")
        return "scrolled"
    except Exception as e:
        log_error(f"scroll failed: {e}")
        return f"scroll failed: {e}"

@mcp.tool()
def type_slow(text: str) -> str:
    try:
        for c in text:
            iv = random.uniform(BASE_INTERVAL, BASE_INTERVAL + TYPE_JITTER)
            pyautogui.write(c, interval=iv)
        time.sleep(random.uniform(0.3, 0.7))
        log_info(f"type_slow: len {len(text)}")
        return "typed"
    except Exception as e:
        log_error(f"type_slow failed: {e}")
        return f"type_slow failed: {e}"

@mcp.tool()
def hotkey(key: str) -> str:
    try:
        pyautogui.hotkey(*key.split("+"))
        time.sleep(random.uniform(0.4, 0.7))
        log_info(f"hotkey: {key}")
        return f"pressed {key}"
    except Exception as e:
        log_error(f"hotkey failed {key}: {e}")
        return f"hotkey failed: {e}"

@mcp.tool()
def wait(sec: float = 1.0) -> str:
    try:
        s = max(0.2, min(5.0, sec))
        time.sleep(s)
        log_info(f"wait: {s:.1f}s")
        return f"waited {s:.1f}s"
    except Exception as e:
        log_error(f"wait failed: {e}")
        return f"wait failed: {e}"

@mcp.tool()
def open_app(app_name: str) -> str:
    try:
        subprocess.run(["open", "-a", app_name], capture_output=True)
        time.sleep(random.uniform(1.5, 3.0))
        log_info(f"open_app: {app_name}")
        return f"opened {app_name}"
    except Exception as e:
        log_error(f"open_app failed {app_name}: {e}")
        return f"open_app failed: {e}"

@mcp.tool()
def activate_app(app_name: str) -> str:
    try:
        script = f'tell application "{app_name}" to activate'
        subprocess.run(["osascript", "-e", script], capture_output=True)
        time.sleep(0.5)
        log_info(f"activate_app: {app_name}")
        return f"activated {app_name}"
    except Exception as e:
        log_error(f"activate_app failed: {e}")
        return f"activate_app failed: {e}"

@mcp.tool()
def get_mouse_pos() -> str:
    try:
        pos = pyautogui.position()
        x, y = pos.x, pos.y
        log_info(f"get_mouse_pos: ({x},{y})")
        return f"mouse at ({x},{y})"
    except Exception as e:
        log_error(f"get_mouse_pos failed: {e}")
        return f"get_mouse_pos failed: {e}"

@mcp.tool()
def fill_password(service: str, account: str) -> str:
    try:
        res = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True, text=True,
        )
        pwd = res.stdout.strip()
        if not pwd:
            tip = f'password not found. run: security add-generic-password -s "{service}" -a "{account}" -w "YOUR_PASSWORD"'
            log_error(f"fill_password failed: {service}")
            return tip
        for char in pwd:
            iv = random.uniform(BASE_INTERVAL, BASE_INTERVAL + TYPE_JITTER)
            pyautogui.write(char, interval=iv)
        log_info(f"fill_password ok: {service}")
        return "password filled"
    except Exception as e:
        log_error(f"fill_password error: {e}")
        return f"fill_password failed: {e}"

def create_authenticated_app(server, *, debug=False):
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        if not check_auth(request):
            return JSONResponse(status_code=401, content={"error": "unauthorized"})
        async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    async def handle_messages(request: Request) -> JSONResponse:
        if not check_auth(request):
            return JSONResponse(status_code=401, content={"error": "unauthorized"})
        return await sse.handle_post_message(request)

    async def health(request: Request) -> JSONResponse:
        return JSONResponse({"status": "ok", "name": "LobsterClaw", "auth": "enabled" if API_KEY else "disabled"})

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/health", endpoint=health),
            Mount("/messages/", app=handle_messages),
        ],
    )

def main():
    parser = argparse.ArgumentParser(description="LobsterClaw MCP Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()

    if not API_KEY:
        print("Warning: LOBSTER_API_KEY not set!")
        confirm = input("Continue without auth? (y/N): ")
        if confirm.lower() != "y":
            return

    mcp_server = getattr(mcp, "_mcp_server", None)
    if mcp_server is None:
        mcp_server = mcp

    app = create_authenticated_app(mcp_server, debug=False)

    print(f"LobsterClaw MCP Server")
    print(f"  URL:    http://{args.host}:{args.port}")
    print(f"  SSE:    http://{args.host}:{args.port}/sse")
    print(f"  Health: http://{args.host}:{args.port}/health")
    print(f"  Auth:   {'enabled' if API_KEY else 'disabled'}")
    print()

    log_info(f"Starting server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")

if __name__ == "__main__":
    main()
