import asyncio
from mcp.client.sse import sse_client

async def test():
    url = "http://127.0.0.1:8000/sse"
    print(f"Connecting to {url}...")
    try:
        async with sse_client(url) as (read, write):
            print("Connected!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
