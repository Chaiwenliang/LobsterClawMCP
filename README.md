macOS 本地 AI 电脑自动化 MCP，专为 OpenClaw / Claude / Cursor 设计。

## 功能
- 屏幕截图
- 真人级鼠标移动（随机轨迹、偏移、缓动）
- 左/右键点击（不永远点中心）
- 滚轮滚动
- 随机间隔打字（中英文/密码均拟人）
- 打开/激活应用
- 快捷键、等待停顿
- 从 Mac 钥匙串安全填充密码（AI 不见明文）
- 找不到密码自动提示添加方法
- 完整操作日志 + 追踪 ID，方便 DEBUG

## 启动
```bash
pip install -r requirements.txt
uvicorn lobster_claw_mcp:app --host 127.0.0.1 --port 8090
```
