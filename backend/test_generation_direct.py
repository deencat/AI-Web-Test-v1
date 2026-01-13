"""Direct test of generation service to see actual errors."""
import asyncio
from app.services.test_generation import TestGenerationService
from app.services.universal_llm import UniversalLLMService
from app.db.session import SessionLocal
from app.core.config import settings

async def test_llm_direct():
    """Test LLM service directly."""
    print("\n" + "="*60)
    print("Testing LLM Service API Keys...")
    print("="*60)
    
    llm = UniversalLLMService()
    print(f"Google API Key: {llm.google_api_key[:20] if llm.google_api_key else None}...")
    print(f"Cerebras API Key: {llm.cerebras_api_key[:20] if llm.cerebras_api_key else None}...")
    print(f"OpenRouter API Key: {llm.openrouter_api_key[:20] if llm.openrouter_api_key else None}...")
    
    print("\n" + "="*60)
    print("Testing simple Google API call...")
    print("="*60)
    
    try:
        messages = [
            {"role": "user", "content": "Say 'Hello, this is a test' and nothing else."}
        ]
        
        result = await llm.chat_completion(
            messages=messages,
            provider="google",
            model="gemini-2.5-flash",
            temperature=0.7,
            max_tokens=50
        )
        
        print("✅ Google API call SUCCESS!")
        print(f"Response: {result['choices'][0]['message']['content'][:100]}")
        
    except Exception as e:
        print(f"❌ Google API call FAILED: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_generation():
    """Test generation with different providers."""
    service = TestGenerationService()
    db = SessionLocal()
    
    try:
        print("\n" + "="*60)
        print("Testing test generation with user settings...")
        print("="*60)
        
        result = await service.generate_tests(
            requirement="User can login with username and password",
            test_type="e2e",
            num_tests=1,
            user_id=1,  # User with settings
            db=db
        )
        
        print("\n✅ SUCCESS!")
        print(f"Generated {len(result.get('test_cases', []))} test case(s)")
        print(f"Model used: {result.get('metadata', {}).get('model')}")
        
    except Exception as e:
        print("\n❌ ERROR:")
        print(f"Type: {type(e).__name__}")
        print(f"Message: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()
    
    finally:
        db.close()

async def main():
    await test_llm_direct()
    await test_generation()

if __name__ == "__main__":
    asyncio.run(main())
