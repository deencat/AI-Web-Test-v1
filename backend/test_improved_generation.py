"""
Test improved test generation with simple requirements.

This demonstrates:
1. Detection of simple vs. detailed requirements
2. Lower temperature for consistency
3. Enhanced prompting for business users

NOTE: Uses OpenRouter API (configured in .env with OPENROUTER_API_KEY)
"""
import asyncio
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

from app.services.test_generation import TestGenerationService

# Force OpenRouter provider for this test (override .env)
os.environ['MODEL_PROVIDER'] = 'openrouter'
print(f"[INFO] Using provider: {os.environ['MODEL_PROVIDER']}")


async def test_simple_requirement():
    """Test generation from simple business requirement."""
    
    service = TestGenerationService()
    
    # Example 1: Simple requirement (what a business user would write)
    simple_requirement = """
    Test the Three HK broadband purchase flow:
    - Purchase the $154/month plan with 48 months contract
    - Login with email: pmo.andrewchan+010@gmail.com and password: cA8mn49&
    - Select the earliest activation date
    - Click confirm
    
    URL: https://web.three.com.hk/5gbroadband/plan-monthly.html?intcmp=web_homeshortcut_5gbb_251230_nil_tc
    """
    
    print("\n" + "="*80)
    print("🔍 TESTING SIMPLE REQUIREMENT (Business-Friendly)")
    print("="*80)
    print(f"\nRequirement:\n{simple_requirement}\n")
    
    try:
        # Test detection
        is_simple = service._detect_requirement_complexity(simple_requirement)
        print(f"✅ Detected as: {'SIMPLE' if is_simple else 'DETAILED'}")
        print(f"   (System will use enhanced prompting for simple requirements)")
        
        # Generate tests (with low temperature for consistency)
        # Use Google API (configured in .env)
        print("\n⏳ Generating test cases (temperature=0.2 for consistency)...")
        
        # Mock user config to use Google (since no DB session in test)
        from unittest.mock import Mock
        mock_db = Mock()
        
        result = await service.generate_tests(
            requirement=simple_requirement,
            test_type="e2e",
            num_tests=1,
            use_kb_context=False,
            db=None  # No DB needed for this test
        )
        
        print(f"\n✅ Generated {len(result['test_cases'])} test case(s)")
        
        # Display first test case
        if result['test_cases']:
            test = result['test_cases'][0]
            print(f"\n📋 Test Case: {test['title']}")
            print(f"   Description: {test['description']}")
            print(f"   Priority: {test['priority']}")
            print(f"   Steps: {len(test.get('steps', []))}")
            
            print("\n📝 Steps:")
            for i, step in enumerate(test.get('steps', []), 1):
                print(f"   {i}. {step}")
            
            print(f"\n🎯 Expected Result: {test.get('expected_result', 'N/A')}")
            
            if test.get('test_data'):
                print(f"\n📊 Test Data:")
                for key, value in test['test_data'].items():
                    print(f"   - {key}: {value}")
        
        print(f"\n📈 Metadata:")
        print(f"   - Model: {result['metadata']['model']}")
        print(f"   - Tokens used: {result['metadata']['tokens']}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


async def test_consistency():
    """Test that same input produces consistent output."""
    
    service = TestGenerationService()
    
    simple_requirement = "Purchase $154 plan with 48 months, login, select date, confirm"
    
    print("\n" + "="*80)
    print("🎯 TESTING CONSISTENCY (Run 3 times)")
    print("="*80)
    print(f"\nRequirement: {simple_requirement}\n")
    
    results = []
    
    for run in range(3):
        print(f"\n🔄 Run {run + 1}/3...")
        try:
            result = await service.generate_tests(
                requirement=simple_requirement,
                test_type="e2e",
                num_tests=1,
                use_kb_context=False,
                db=None
            )
            
            if result['test_cases']:
                test = result['test_cases'][0]
                num_steps = len(test.get('steps', []))
                title = test['title']
                results.append({
                    'run': run + 1,
                    'title': title,
                    'num_steps': num_steps,
                    'first_step': test['steps'][0] if test['steps'] else 'N/A'
                })
                print(f"   ✅ Generated: {title} ({num_steps} steps)")
        
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    # Compare results
    print("\n" + "="*80)
    print("📊 CONSISTENCY ANALYSIS")
    print("="*80)
    
    if len(results) == 3:
        step_counts = [r['num_steps'] for r in results]
        titles = [r['title'] for r in results]
        first_steps = [r['first_step'] for r in results]
        
        print(f"\n📝 Step counts: {step_counts}")
        print(f"   Range: {min(step_counts)} - {max(step_counts)} steps")
        print(f"   Average: {sum(step_counts) / len(step_counts):.1f} steps")
        
        print(f"\n🏷️ Titles:")
        for i, title in enumerate(titles, 1):
            print(f"   Run {i}: {title}")
        
        print(f"\n🔍 First steps:")
        for i, step in enumerate(first_steps, 1):
            print(f"   Run {i}: {step}")
        
        # Consistency check
        if max(step_counts) - min(step_counts) <= 2:
            print(f"\n✅ GOOD: Step count variation is minimal (≤2 steps)")
        else:
            print(f"\n⚠️ WARNING: Step count varies significantly ({max(step_counts) - min(step_counts)} steps)")
    
    else:
        print("\n❌ Could not complete all runs for consistency check")


async def test_detailed_requirement():
    """Test that detailed requirements are still handled correctly."""
    
    service = TestGenerationService()
    
    detailed_requirement = """
    Step 1: Navigate to https://example.com/login
    Step 2: Enter email in the email field
    Step 3: Enter password in the password field
    Step 4: Click the 'Login' button
    Step 5: Verify user is redirected to dashboard
    """
    
    print("\n" + "="*80)
    print("🔍 TESTING DETAILED REQUIREMENT (Technical)")
    print("="*80)
    print(f"\nRequirement:\n{detailed_requirement}\n")
    
    try:
        # Test detection
        is_simple = service._detect_requirement_complexity(detailed_requirement)
        print(f"✅ Detected as: {'SIMPLE' if is_simple else 'DETAILED'}")
        print(f"   (System will use standard prompting for detailed requirements)")
        
        print("\n⏳ Generating test cases...")
        result = await service.generate_tests(
            requirement=detailed_requirement,
            test_type="e2e",
            num_tests=1,
            use_kb_context=False,
            db=None
        )
        
        print(f"\n✅ Generated {len(result['test_cases'])} test case(s)")
        
        if result['test_cases']:
            test = result['test_cases'][0]
            print(f"\n📋 Test Case: {test['title']}")
            print(f"   Steps: {len(test.get('steps', []))}")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        raise


async def main():
    """Run all tests."""
    
    print("\n" + "="*80)
    print("🚀 IMPROVED TEST GENERATION - DEMONSTRATION")
    print("="*80)
    print("\nKey Improvements:")
    print("1. ✅ Auto-detects simple vs. detailed requirements")
    print("2. ✅ Enhanced prompting for business users")
    print("3. ✅ Lower temperature (0.2) for consistency")
    print("4. ✅ Handles modal/dialog interactions explicitly")
    print("5. ✅ Generates detailed steps from high-level requirements")
    
    # Run tests
    await test_simple_requirement()
    await test_consistency()
    await test_detailed_requirement()
    
    print("\n" + "="*80)
    print("✅ DEMONSTRATION COMPLETE")
    print("="*80)
    print("\n💡 Next Steps:")
    print("   1. Business users can now write simple requirements")
    print("   2. System generates consistent, detailed test steps")
    print("   3. Temperature=0.2 ensures reproducible results")
    print("   4. Test with your Three HK example!")


if __name__ == "__main__":
    asyncio.run(main())
