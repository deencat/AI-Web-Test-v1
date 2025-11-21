"""Run all Day 2 verification tests."""
import subprocess
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Change to backend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

tests = [
    ("OpenRouter Integration", "test_openrouter.py"),
    ("Test Generation Service", "test_generation_service.py"),
]

def main():
    print("=" * 80)
    print("DAY 2 VERIFICATION - Running All Tests")
    print("=" * 80)
    
    results = []
    
    for name, script in tests:
        print(f"\n[Testing] {name}...")
        print("-" * 80)
        
        result = subprocess.run(
            [sys.executable, script],
            capture_output=True,
            text=True
        )
        
        success = result.returncode == 0
        results.append((name, success))
        
        if success:
            print(f"[OK] {name} - PASSED")
            # Show last few lines of output
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines[-5:]:
                    if line.strip():
                        print(f"  {line}")
        else:
            print(f"[X] {name} - FAILED")
            print("\nOutput:")
            print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
            if result.stderr:
                print("\nErrors:")
                print(result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    
    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "[OK] PASSED" if success else "[X] FAILED"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 80)
    if passed == total:
        print(f"[OK] ALL TESTS PASSED ({passed}/{total})")
        print("[OK] Day 2 is VERIFIED and ready for Day 3!")
        print("\n📋 Next Steps:")
        print("  1. Review sample_generated_tests.json for quality")
        print("  2. Proceed to Day 3: Database models and API endpoints")
        print("  3. Check DAY-2-VERIFICATION-CHECKLIST.md")
        return True
    else:
        print(f"[X] SOME TESTS FAILED ({passed}/{total} passed)")
        print("[!] Please fix issues before proceeding to Day 3")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[X] Verification script error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

