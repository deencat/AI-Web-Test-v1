"""
Test script for Sprint 5.5 Day 2: Settings API Endpoints
Tests all execution settings API endpoints
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# API base URL
API_BASE_URL = "http://localhost:8000/api/v1"

# Test credentials (assuming you have a test user)
TEST_USERNAME = "testuser"
TEST_PASSWORD = "testpassword123"


async def get_auth_token():
    """Get JWT token for authentication"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/auth/login",
            data={
                "username": TEST_USERNAME,
                "password": TEST_PASSWORD
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["access_token"]
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None


async def test_get_execution_settings(token: str):
    """Test GET /api/v1/settings/execution"""
    print("\n" + "=" * 60)
    print("TEST 1: GET /api/v1/settings/execution")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/settings/execution",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Settings retrieved:")
            print(f"  - Strategy: {data['fallback_strategy']}")
            print(f"  - Timeout: {data['timeout_per_tier_seconds']}s")
            print(f"  - Max retries: {data['max_retry_per_tier']}")
            print(f"  - Track effectiveness: {data['track_strategy_effectiveness']}")
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None


async def test_update_execution_settings(token: str):
    """Test PUT /api/v1/settings/execution"""
    print("\n" + "=" * 60)
    print("TEST 2: PUT /api/v1/settings/execution")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Update to Option A
    update_data = {
        "fallback_strategy": "option_a",
        "timeout_per_tier_seconds": 45
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{API_BASE_URL}/settings/execution",
            headers=headers,
            json=update_data
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Settings updated:")
            print(f"  - Strategy: {data['fallback_strategy']}")
            print(f"  - Timeout: {data['timeout_per_tier_seconds']}s")
            
            # Verify update
            assert data['fallback_strategy'] == "option_a", "Strategy should be updated"
            assert data['timeout_per_tier_seconds'] == 45, "Timeout should be updated"
            print("✅ Update verified")
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None


async def test_get_available_strategies(token: str):
    """Test GET /api/v1/settings/execution/strategies"""
    print("\n" + "=" * 60)
    print("TEST 3: GET /api/v1/settings/execution/strategies")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/settings/execution/strategies",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {len(data)} strategies available:")
            
            for strategy in data:
                print(f"\n  {strategy['display_name']}")
                print(f"    - Success rate: {strategy['success_rate_min']}-{strategy['success_rate_max']}%")
                print(f"    - Cost: {strategy['cost_level']}")
                print(f"    - Recommended: {'✅' if strategy['recommended'] else '⚪'}")
                print(f"    - Flow: {' → '.join(['Tier ' + str(t) for t in strategy['tier_flow']])}")
            
            assert len(data) == 3, "Should have 3 strategies"
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None


async def test_tier_distribution(token: str):
    """Test GET /api/v1/settings/analytics/tier-distribution"""
    print("\n" + "=" * 60)
    print("TEST 4: GET /api/v1/settings/analytics/tier-distribution")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/settings/analytics/tier-distribution",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tier distribution statistics:")
            print(f"  - Total executions: {data['total_executions']}")
            print(f"  - Overall success rate: {data['overall_success_rate']}%")
            print(f"  - Tier 1 success: {data['tier1_success']}")
            print(f"  - Tier 2 success: {data['tier2_success']}")
            print(f"  - Tier 3 success: {data['tier3_success']}")
            
            if data['total_executions'] > 0:
                print(f"  - Avg Tier 1 time: {data['avg_tier1_time_ms']:.2f}ms")
                print(f"  - Avg Tier 2 time: {data['avg_tier2_time_ms']:.2f}ms")
                print(f"  - Avg Tier 3 time: {data['avg_tier3_time_ms']:.2f}ms")
            else:
                print("  ⚠️ No execution data yet")
            
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None


async def test_strategy_effectiveness(token: str):
    """Test GET /api/v1/settings/analytics/strategy-effectiveness"""
    print("\n" + "=" * 60)
    print("TEST 5: GET /api/v1/settings/analytics/strategy-effectiveness")
    print("=" * 60)
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/settings/analytics/strategy-effectiveness",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if len(data) == 0:
                print("  ⚠️ No strategy data yet (no executions with 3-Tier engine)")
                return data
            
            print(f"✅ Strategy effectiveness for {len(data)} strategies:")
            
            for strategy in data:
                print(f"\n  Strategy: {strategy['strategy']}")
                print(f"    - Total executions: {strategy['total_executions']}")
                print(f"    - Success rate: {strategy['success_rate']}%")
                print(f"    - Avg time: {strategy['avg_execution_time_ms']:.2f}ms")
                print(f"    - Tier 1: {strategy['tier1_percentage']}%")
                print(f"    - Tier 2: {strategy['tier2_percentage']}%")
                print(f"    - Tier 3: {strategy['tier3_percentage']}%")
                print(f"    - Cost estimate: {strategy['cost_estimate']}")
            
            return data
        else:
            print(f"❌ Failed: {response.text}")
            return None


async def main():
    """Run all API endpoint tests"""
    print("\n" + "=" * 60)
    print("Sprint 5.5 Day 2: Settings API Endpoints Test Suite")
    print("=" * 60)
    
    print("\n🔐 Authenticating...")
    token = await get_auth_token()
    
    if not token:
        print("\n❌ Authentication failed. Make sure:")
        print("  1. Backend server is running")
        print("  2. Test user exists (username: testuser, password: testpassword123)")
        print("  3. Database is properly initialized")
        return 1
    
    print(f"✅ Authenticated successfully")
    
    try:
        # Test 1: Get execution settings
        settings = await test_get_execution_settings(token)
        if not settings:
            return 1
        
        # Test 2: Update execution settings
        updated_settings = await test_update_execution_settings(token)
        if not updated_settings:
            return 1
        
        # Test 3: Get available strategies
        strategies = await test_get_available_strategies(token)
        if not strategies:
            return 1
        
        # Test 4: Get tier distribution
        tier_stats = await test_tier_distribution(token)
        if tier_stats is None:
            return 1
        
        # Test 5: Get strategy effectiveness
        strategy_stats = await test_strategy_effectiveness(token)
        if strategy_stats is None:
            return 1
        
        print("\n" + "=" * 60)
        print("🎉 ALL API TESTS PASSED!")
        print("=" * 60)
        print("\n✅ GET /api/v1/settings/execution")
        print("✅ PUT /api/v1/settings/execution")
        print("✅ GET /api/v1/settings/execution/strategies")
        print("✅ GET /api/v1/settings/analytics/tier-distribution")
        print("✅ GET /api/v1/settings/analytics/strategy-effectiveness")
        print("\n" + "=" * 60)
        print("Day 2 API Endpoints: Complete")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
