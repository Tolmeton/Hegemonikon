import asyncio
import sys
sys.path.insert(0, '.')
from mekhane.ochema.cortex_client import CortexClient

async def test():
    client = CortexClient()
    print('asking...')
    try:
        res = await asyncio.wait_for(client.ask_async('test', 'gemini-3.1-pro-preview'), timeout=15)
        print("Success:", res.text[:100])
    except asyncio.TimeoutError:
        print("Timeout Error!")
    except Exception as e:
        print("Error:", e)

if __name__ == '__main__':
    asyncio.run(test())
