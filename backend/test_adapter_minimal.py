import asyncio
import sys
sys.path.insert(0, 'C:\\Users\\andrechw\\Documents\\AI-Web-Test-v1-1\\backend')

from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter

async def test():
    adapter = TypeScriptStagehandAdapter(
        service_url="http://localhost:3001"
    )
    adapter.test_case_id = 1  # Set as attribute
    
    print("Initializing adapter...")
    await adapter.initialize({"model": "gpt-4", "temperature": 0.7})
    print("Success!")

if __name__ == "__main__":
    asyncio.run(test())
