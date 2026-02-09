"""
Test 3-Tier Execution Engine Integration
Tests real test execution with the integrated 3-tier system
"""
import asyncio
import sys
sys.path.insert(0, '.')

from app.db.session import SessionLocal
from app.models.test_case import TestCase
from app.models.execution_settings import ExecutionSettings
from app.services.execution_service import ExecutionService


async def test_3tier_integration():
    """Test 3-tier execution with a real test case"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("🧪 Testing 3-Tier Execution Engine Integration")
        print("=" * 80)
        
        # Get a test case from database
        test_case = db.query(TestCase).first()
        
        if not test_case:
            print('❌ No test cases found in database')
            print('   Create a test case first using the frontend UI')
            return
        
        print(f'\n✅ Found test case: {test_case.title} (ID: {test_case.id})')
        print(f'   User ID: {test_case.user_id}')
        print(f'   Type: {test_case.test_type}')
        print(f'   Priority: {test_case.priority}')
        
        # Check steps
        import json
        steps = test_case.steps if isinstance(test_case.steps, list) else json.loads(test_case.steps)
        print(f'   Steps: {len(steps)}')
        for i, step in enumerate(steps[:3], 1):  # Show first 3 steps
            print(f'     {i}. {step}')
        if len(steps) > 3:
            print(f'     ... and {len(steps) - 3} more steps')
        
        # Check if user has execution settings
        print(f'\n🔍 Checking execution settings...')
        settings = db.query(ExecutionSettings).filter(
            ExecutionSettings.user_id == test_case.user_id
        ).first()
        
        if settings:
            print(f'✅ User has configured execution settings:')
            print(f'   Strategy: {settings.fallback_strategy}')
            print(f'   Timeout per tier: {settings.timeout_per_tier_seconds}s')
            print(f'   Max retry per tier: {settings.max_retry_per_tier}')
            print(f'   Track fallback: {settings.track_fallback_reasons}')
            print(f'   Track strategy effectiveness: {settings.track_strategy_effectiveness}')
        else:
            print(f'⚠️  User has no execution settings configured')
            print(f'   Will use default settings: option_c (Tier 1→2→3)')
        
        print(f'\n🚀 Initializing execution service with 3-tier engine...')
        service = ExecutionService()
        
        # Extract base URL from first step if it contains a URL
        import re
        base_url = 'http://localhost:3000'  # Default
        if steps:
            first_step = steps[0]
            urls = re.findall(r'https?://[^\s]+', first_step)
            if urls:
                base_url = urls[0]
                print(f'   Extracted base URL from steps: {base_url}')
        
        print(f'\n▶️  Starting test execution...')
        print(f'   This will attempt:')
        print(f'   - Tier 1: Direct Playwright execution (fastest)')
        if not settings or settings.fallback_strategy == 'option_c':
            print(f'   - Tier 2: Hybrid mode (if Tier 1 fails)')
            print(f'   - Tier 3: Stagehand act() (if Tier 2 fails)')
        elif settings and settings.fallback_strategy == 'option_a':
            print(f'   - Tier 2: Hybrid mode (if Tier 1 fails)')
        elif settings and settings.fallback_strategy == 'option_b':
            print(f'   - Tier 3: Stagehand act() (if Tier 1 fails)')
        
        print(f'\n' + '─' * 80)
        
        # Execute the test
        execution = await service.execute_test(
            db=db,
            test_case=test_case,
            user_id=test_case.user_id,
            base_url=base_url
        )
        
        print(f'\n' + '─' * 80)
        print(f'\n✅ Execution completed!')
        print(f'\n📊 Results:')
        print(f'   Execution ID: {execution.id}')
        print(f'   Result: {execution.result}')
        print(f'   Total steps: {execution.total_steps}')
        print(f'   Passed steps: {execution.passed_steps}')
        print(f'   Failed steps: {execution.failed_steps}')
        print(f'   Duration: {execution.duration_seconds:.2f}s')
        
        # Check execution steps for tier information
        print(f'\n🔍 Checking step execution details...')
        from app.crud import test_execution as crud_execution
        exec_steps = crud_execution.get_execution_steps(db, execution.id)
        
        if exec_steps:
            print(f'   Found {len(exec_steps)} execution steps')
            for step in exec_steps[:3]:  # Show first 3
                print(f'   Step {step.step_number}: {step.result.value}')
                if step.error_message:
                    print(f'      Error: {step.error_message[:100]}...')
        
        # Check feedback entries for tier information
        print(f'\n🔍 Checking execution feedback with tier info...')
        from app.crud import execution_feedback as crud_feedback
        feedback_entries = crud_feedback.get_feedback_by_execution(db, execution.id)
        
        if feedback_entries:
            print(f'   Found {len(feedback_entries)} feedback entries')
            for fb in feedback_entries[:2]:  # Show first 2
                print(f'   Feedback #{fb.id}:')
                print(f'      Failure type: {fb.failure_type}')
                if fb.metadata:
                    import json
                    # Handle both dict and JSON string
                    try:
                        if isinstance(fb.metadata, dict):
                            metadata = fb.metadata
                        elif isinstance(fb.metadata, str):
                            metadata = json.loads(fb.metadata)
                        else:
                            # It's a SQLAlchemy type, get the value
                            metadata = dict(fb.metadata) if hasattr(fb.metadata, '__iter__') else {}
                        
                        if metadata:
                            if 'strategy_used' in metadata:
                                print(f'      Strategy used: {metadata["strategy_used"]}')
                            if 'tiers_attempted' in metadata:
                                print(f'      Tiers attempted: {metadata["tiers_attempted"]}')
                            if 'final_failed_tier' in metadata:
                                print(f'      Final failed tier: {metadata["final_failed_tier"]}')
                    except Exception as meta_error:
                        print(f'      (Could not parse metadata: {meta_error})')
        else:
            print(f'   No feedback entries (all steps may have succeeded)')
        
        print(f'\n' + '=' * 80)
        print(f'✅ 3-Tier Integration Test Complete!')
        print(f'=' * 80)
        
    except Exception as e:
        print(f'\n❌ Error during test: {e}')
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_3tier_integration())
