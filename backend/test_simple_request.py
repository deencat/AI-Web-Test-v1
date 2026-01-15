import asyncio
import aiohttp
import json

async def test_request():
    payload = {
        "session_id": "test-abc123",
        "test_id": 1,
        "user_id": 1,
        "config": {}
    }
    
    print(f"Sending: {json.dumps(payload, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:3001/api/sessions/initialize",
            json=payload
        ) as response:
            print(f"\nStatus: {response.status}")
            text = await response.text()
            print(f"Response: {text}")

if __name__ == "__main__":
    asyncio.run(test_request())
