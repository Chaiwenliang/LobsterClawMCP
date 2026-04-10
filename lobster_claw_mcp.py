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
    handler = RotatingFileHandler(log_path, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8")
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
def fill_password(service: str, account: str) -> str:
    try:
        res = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            capture_output=True,
            text=True,
        )
        if res.returncode != 0:
            hint = f'security add-generic-password -s "{service}" -a "{account}" -w "<your_password>"'
            log_info(f"fill_password: 未找到 {service}/{account}")
            return f"❌ 未找到密码 {service}/{account}\n👉 可用如下方式添加：\n{hint}"
        pwd = res.stdout.rstrip("\n")
        for c in pwd:
            iv = random.uniform(BASE_INTERVAL, BASE_INTERVAL + TYPE_JITTER)
            pyautogui.write(c, interval=iv)
        time.sleep(random.uniform(0.2, 0.4))
        log_info(f"fill_password: 已输入 {service}/{account}")
        return "✅ 已安全填充密码"
    except Exception as e:
        log_error(f"fill_password 失败 {service}/{account}: {e}")
        return "❌ 填充密码失败"


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


def create_starlette_app(server, *, debug: bool = False) -> Starlette:
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(request.scope, request.receive, request._send) as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    async def health() -> JSONResponse:
        return JSONResponse({"status": "ok", "name": "LobsterClaw"})

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Route("/health", endpoint=health),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )


mcp_server = getattr(mcp, "_mcp_server", None)
if mcp_server is None:
    mcp_server = mcp

app = create_starlette_app(mcp_server, debug=False)


@mcp.tool()
def fill_password(service: str, account: str) -> str:
    """
    安全地从 macOS 钥匙串中获取并自动输入密码。
    AI 不会看到明文密码。
    """
    try:
        cmd = f'security find-generic-password -s "{service}" -a "{account}" -w'
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        pwd = res.stdout.strip()

        if not pwd:
            tip = f'❌ 找不到密码。请在终端运行: security add-generic-password -s "{service}" -a "{account}" -w "YOUR_PASSWORD"'
            log_error(f"fill_password 失败: 找不到 {service} 的密码")
            return tip

        # 模拟真人输入
        for char in pwd:
            iv = random.uniform(BASE_INTERVAL, BASE_INTERVAL + TYPE_JITTER)
            pyautogui.write(char, interval=iv)

        log_info(f"fill_password 成功: 已填充 {service} 的密码")
        return "✅ 密码已安全填充"
    except Exception as e:
        log_error(f"fill_password 异常: {e}")
        return f"❌ 填充失败: {e}"


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run LobsterClaw MCP server")
    parser.add_argument("--sse", action="store_true", help="Run as SSE server instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args()

    if args.sse:
        import uvicorn
        log_info(f"Starting SSE server on {args.host}:{args.port}")
        uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    else:
        # Trae/Claude/Cursor 默认使用 stdio 管道
        # 使用 mcp.run() 可以让 IDE 直接识别，避免卡在“准备中”
        mcp.run()


if __name__ == "__main__":
    main()