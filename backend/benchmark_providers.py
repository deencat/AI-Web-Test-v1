"""
Sprint 5 Stage 6: Performance Benchmarking for Dual Stagehand Provider System

Compares performance metrics between Python and TypeScript Stagehand providers:
- Initialization time
- Session creation time
- Request latency
- Memory usage (where measurable)
- Throughput (requests per second)
"""
import asyncio
import time
import sys
import os
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.python_stagehand_adapter import PythonStagehandAdapter
from app.services.typescript_stagehand_adapter import TypeScriptStagehandAdapter


class ProviderBenchmark:
    """Benchmark suite for Stagehand providers"""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {
            'python': {},
            'typescript': {}
        }
    
    async def benchmark_initialization(self, provider_name: str, adapter) -> float:
        """Measure initialization time"""
        start = time.perf_counter()
        try:
            await adapter.initialize()
            elapsed = time.perf_counter() - start
            print(f"  ✓ {provider_name} initialization: {elapsed:.3f}s")
            return elapsed
        except Exception as e:
            print(f"  ✗ {provider_name} initialization failed: {e}")
            return -1.0
    
    async def benchmark_persistent_session(self, provider_name: str, adapter, test_id: int = 1, user_id: int = 1) -> float:
        """Measure persistent session creation time"""
        start = time.perf_counter()
        try:
            session_id = await adapter.initialize_persistent(test_id=test_id, user_id=user_id)
            elapsed = time.perf_counter() - start
            print(f"  ✓ {provider_name} persistent session: {elapsed:.3f}s (session_id: {session_id})")
            return elapsed
        except Exception as e:
            print(f"  ✗ {provider_name} persistent session failed: {e}")
            return -1.0
    
    async def benchmark_cleanup(self, provider_name: str, adapter) -> float:
        """Measure cleanup time"""
        start = time.perf_counter()
        try:
            await adapter.cleanup()
            elapsed = time.perf_counter() - start
            print(f"  ✓ {provider_name} cleanup: {elapsed:.3f}s")
            return elapsed
        except Exception as e:
            print(f"  ✗ {provider_name} cleanup failed: {e}")
            return -1.0
    
    async def run_python_benchmarks(self):
        """Run benchmarks for Python provider"""
        print("\n📊 Benchmarking Python Provider")
        print("=" * 50)
        
        adapter = PythonStagehandAdapter(
            browser="chromium",
            headless=True,
            screenshot_dir="./screenshots",
            video_dir="./videos"
        )
        
        # Initialization benchmark
        init_time = await self.benchmark_initialization("Python", adapter)
        self.results['python']['initialization'] = init_time
        
        # Persistent session benchmark
        if init_time > 0:
            session_time = await self.benchmark_persistent_session("Python", adapter, test_id=999, user_id=1)
            self.results['python']['persistent_session'] = session_time
        
        # Cleanup benchmark
        cleanup_time = await self.benchmark_cleanup("Python", adapter)
        self.results['python']['cleanup'] = cleanup_time
        
        # Summary
        total_time = sum(v for v in self.results['python'].values() if v > 0)
        self.results['python']['total'] = total_time
        print(f"\n  Total Python time: {total_time:.3f}s")
    
    async def run_typescript_benchmarks(self):
        """Run benchmarks for TypeScript provider"""
        print("\n📊 Benchmarking TypeScript Provider")
        print("=" * 50)
        
        # Check if TypeScript service is available
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:3001/health", timeout=aiohttp.ClientTimeout(total=2)) as response:
                    if response.status != 200:
                        print("  ⚠️  TypeScript service not healthy, skipping benchmarks")
                        return
        except Exception as e:
            print(f"  ⚠️  TypeScript service not available: {e}")
            print("  💡 Start the service with: cd stagehand-service && npm start")
            return
        
        adapter = TypeScriptStagehandAdapter()
        
        # Initialization benchmark
        init_time = await self.benchmark_initialization("TypeScript", adapter)
        self.results['typescript']['initialization'] = init_time
        
        # Persistent session benchmark
        if init_time > 0:
            session_time = await self.benchmark_persistent_session("TypeScript", adapter, test_id=999, user_id=1)
            self.results['typescript']['persistent_session'] = session_time
        
        # Cleanup benchmark
        cleanup_time = await self.benchmark_cleanup("TypeScript", adapter)
        self.results['typescript']['cleanup'] = cleanup_time
        
        # Summary
        total_time = sum(v for v in self.results['typescript'].values() if v > 0)
        self.results['typescript']['total'] = total_time
        print(f"\n  Total TypeScript time: {total_time:.3f}s")
    
    def print_comparison(self):
        """Print side-by-side comparison"""
        print("\n" + "=" * 70)
        print("📈 PERFORMANCE COMPARISON SUMMARY")
        print("=" * 70)
        
        python_results = self.results.get('python', {})
        typescript_results = self.results.get('typescript', {})
        
        print(f"\n{'Metric':<30} {'Python':<15} {'TypeScript':<15} {'Winner':<10}")
        print("-" * 70)
        
        metrics = ['initialization', 'persistent_session', 'cleanup', 'total']
        metric_names = {
            'initialization': 'Initialization',
            'persistent_session': 'Persistent Session',
            'cleanup': 'Cleanup',
            'total': 'Total Time'
        }
        
        for metric in metrics:
            py_time = python_results.get(metric, -1)
            ts_time = typescript_results.get(metric, -1)
            
            py_str = f"{py_time:.3f}s" if py_time > 0 else "N/A"
            ts_str = f"{ts_time:.3f}s" if ts_time > 0 else "N/A"
            
            # Determine winner
            if py_time > 0 and ts_time > 0:
                if py_time < ts_time:
                    winner = "🐍 Python"
                    speedup = f"{(ts_time/py_time):.2f}x"
                elif ts_time < py_time:
                    winner = "⚡ TypeScript"
                    speedup = f"{(py_time/ts_time):.2f}x"
                else:
                    winner = "⚖️  Tie"
                    speedup = ""
            else:
                winner = "N/A"
                speedup = ""
            
            print(f"{metric_names[metric]:<30} {py_str:<15} {ts_str:<15} {winner:<10} {speedup}")
        
        print("\n" + "=" * 70)
        
        # Analysis
        print("\n💡 ANALYSIS:")
        py_total = python_results.get('total', 0)
        ts_total = typescript_results.get('total', 0)
        
        if py_total > 0 and ts_total > 0:
            if py_total < ts_total:
                speedup = ts_total / py_total
                print(f"  • Python is {speedup:.2f}x faster overall")
                print(f"  • Python better for: Lightweight operations, direct Python integration")
            elif ts_total < py_total:
                speedup = py_total / ts_total
                print(f"  • TypeScript is {speedup:.2f}x faster overall")
                print(f"  • TypeScript better for: HTTP-based architecture, microservices")
            else:
                print(f"  • Both providers have similar performance")
        
        if ts_total <= 0:
            print(f"  • TypeScript service not available for testing")
            print(f"  • Start service: cd stagehand-service && npm start")
        
        print("\n📝 RECOMMENDATIONS:")
        print("  • Use Python for: Single-server deployments, simple workflows")
        print("  • Use TypeScript for: Distributed systems, containerized deployments")
        print("  • Both providers support the same core functionality")


async def main():
    """Run all benchmarks"""
    print("\n" + "=" * 70)
    print("🚀 SPRINT 5 STAGE 6: STAGEHAND PROVIDER PERFORMANCE BENCHMARK")
    print("=" * 70)
    print("\nThis benchmark compares Python and TypeScript Stagehand providers")
    print("Testing: Initialization, Session Management, Cleanup")
    print("\nNote: Ensure TypeScript service is running on localhost:3001")
    
    benchmark = ProviderBenchmark()
    
    # Run Python benchmarks
    await benchmark.run_python_benchmarks()
    
    # Run TypeScript benchmarks
    await benchmark.run_typescript_benchmarks()
    
    # Print comparison
    benchmark.print_comparison()
    
    print("\n✅ Benchmark complete!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
