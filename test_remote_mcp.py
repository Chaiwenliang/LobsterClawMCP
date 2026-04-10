import asyncio
import httpx
import sys

async def test_auth():
    url = "http://127.0.0.1:8090"
    api_key = "test-secret-key"
    
    print("--- 1. 测试健康检查 (无认证) ---")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{url}/health")
            print(f"Health Status: {resp.status_code}")
            print(f"Body: {resp.json()}")
        except Exception as e:
            print(f"Error: {e}")

    print("\n--- 2. 测试 SSE 连接 (无 API Key) ---")
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{url}/sse")
        print(f"SSE (No Auth) Status: {resp.status_code}")
        if resp.status_code == 401:
            print("✅ 正确拦截了无认证请求")

    print("\n--- 3. 测试 SSE 连接 (URL 参数认证) ---")
    # SSE 通常是流式的，我们只测试握手是否成功
    async with httpx.AsyncClient() as client:
        try:
            # 使用 timeout=1 快速测试握手
            async with client.stream("GET", f"{url}/sse?api_key={api_key}") as response:
                print(f"SSE (Query Auth) Status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ 认证成功")
        except Exception as e:
            print(f"Handshake error: {e}")

    print("\n--- 4. 测试 SSE 连接 (Bearer Header 认证) ---")
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("GET", f"{url}/sse", headers=headers) as response:
                print(f"SSE (Header Auth) Status: {response.status_code}")
                if response.status_code == 200:
                    print("✅ 认证成功")
        except Exception as e:
            print(f"Handshake error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth())
