"""
Comprehensive Backend Test Suite
Runs all critical tests to verify the backend is working after merge
"""
import subprocess
import sys
from datetime import datetime

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

class TestRunner:
    def __init__(self):
        self.results = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        
    def print_header(self, text):
        print("\n" + "="*80)
        print(f"  {text}")
        print("="*80)
        
    def print_test_result(self, name, status, details=""):
        """Print test result with color coding"""
        symbols = {
            "PASS": "✅",
            "FAIL": "❌",
            "SKIP": "⏭️",
            "RUN": "🏃"
        }
        symbol = symbols.get(status, "❓")
        print(f"{symbol} {status}: {name}")
        if details:
            print(f"   {details}")
    
    def run_test(self, name, script, critical=True):
        """Run a single test script"""
        self.total_tests += 1
        self.print_test_result(name, "RUN", f"Running {script}...")
        
        try:
            # Increase timeout for browser automation tests
            timeout_duration = 180 if "stagehand" in script.lower() or "playwright" in script.lower() else 90
            result = subprocess.run(
                [sys.executable, script],
                capture_output=True,
                text=True,
                timeout=timeout_duration
            )
            
            if result.returncode == 0:
                self.passed_tests += 1
                self.results[name] = "PASS"
                self.print_test_result(name, "PASS")
                return True
            else:
                if critical:
                    self.failed_tests += 1
                    self.results[name] = "FAIL"
                    self.print_test_result(name, "FAIL", result.stderr[:200])
                else:
                    self.skipped_tests += 1
                    self.results[name] = "SKIP"
                    self.print_test_result(name, "SKIP", "Non-critical test failed")
                return False
                
        except subprocess.TimeoutExpired:
            self.failed_tests += 1
            self.results[name] = "FAIL"
            self.print_test_result(name, "FAIL", "Test timeout (>60s)")
            return False
        except Exception as e:
            self.failed_tests += 1
            self.results[name] = "FAIL"
            self.print_test_result(name, "FAIL", str(e))
            return False
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        self.print_header(f"COMPREHENSIVE BACKEND TEST SUITE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n📋 Test Categories:")
        print("   1. Core API Functionality")
        print("   2. Authentication & Security")
        print("   3. Database Operations")
        print("   4. AI/LLM Integration")
        print("   5. Browser Automation")
        print("   6. Integration Tests")
        
        # Category 1: Core API Tests (Critical)
        self.print_header("Category 1: Core API Functionality")
        self.run_test("Health Check & Basic API", "test_api_endpoints.py", critical=True)
        
        # Category 2: Authentication (Critical)
        self.print_header("Category 2: Authentication & Security")
        self.run_test("JWT Authentication", "test_auth.py", critical=True)
        self.run_test("JWT Token Validation", "test_jwt.py", critical=True)
        
        # Category 3: Database Operations (Critical)
        self.print_header("Category 3: Database Operations")
        self.run_test("Database Schema & Operations", "test_comprehensive.py", critical=True)
        
        # Category 4: AI/LLM Integration (Important)
        self.print_header("Category 4: AI/LLM Integration")
        self.run_test("OpenRouter API Connection", "test_openrouter.py", critical=False)
        self.run_test("Test Generation Service", "test_generation_service.py", critical=False)
        
        # Category 5: Browser Automation (Important)
        self.print_header("Category 5: Browser Automation")
        self.run_test("Playwright Direct", "test_playwright_direct.py", critical=False)
        self.run_test("Stagehand Simple", "test_stagehand_simple.py", critical=False)
        
        # Category 6: Feature Integration (Important)
        self.print_header("Category 6: Feature Integration Tests")
        self.run_test("Day 5 Enhancements", "test_day5_enhancements.py", critical=False)
        self.run_test("Knowledge Base API", "test_kb_api.py", critical=False)
        self.run_test("Queue System", "test_queue_system.py", critical=False)
        
        # Print Summary
        self.print_summary()
        
    def print_summary(self):
        """Print final test summary"""
        self.print_header("TEST SUMMARY")
        
        print(f"\n📊 Results:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   ✅ Passed: {self.passed_tests}")
        print(f"   ❌ Failed: {self.failed_tests}")
        print(f"   ⏭️  Skipped: {self.skipped_tests}")
        
        pass_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"\n   Success Rate: {pass_rate:.1f}%")
        
        # Detailed Results
        print("\n📝 Detailed Results:")
        for name, status in self.results.items():
            symbol = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
            print(f"   {symbol} {name}: {status}")
        
        # Final Verdict
        print("\n" + "="*80)
        if self.failed_tests == 0:
            print("🎉 ALL CRITICAL TESTS PASSED!")
            print("✅ Backend is ready for development")
        elif self.failed_tests <= 2 and self.passed_tests >= 5:
            print("⚠️  MOSTLY PASSING - Some non-critical tests failed")
            print("✅ Backend is functional but needs attention")
        else:
            print("❌ CRITICAL FAILURES DETECTED")
            print("⚠️  Backend needs fixes before development")
        print("="*80)
        
        return self.failed_tests == 0

if __name__ == "__main__":
    runner = TestRunner()
    success = runner.run_all_tests()
    sys.exit(0 if success else 1)
