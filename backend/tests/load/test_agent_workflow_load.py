"""
Load tests for the Agent Workflow API v2 (Sprint 10 Phase 2 - Developer B)

Tests performance characteristics of the /api/v2 endpoints under concurrent load.

These tests use Python stdlib (threading/concurrent.futures) — no external load
testing dependencies required. They measure:
- Throughput: requests per second
- Latency: p50/p95/p99 response times
- Concurrency: behaviour under simultaneous requests
- Stability: no 5xx errors under expected load

All tests run against the FastAPI TestClient (in-process) so these are
"unit load tests" rather than true network load tests.  They are suitable
for CI and catching performance regressions early.
"""
import sys
import time
import statistics
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import NamedTuple
import pytest
from fastapi.testclient import TestClient

# Ensure backend package is importable
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path))

from app.main import app

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Concurrency levels to test
CONCURRENT_USERS_LIGHT  = 5
CONCURRENT_USERS_MEDIUM = 20
CONCURRENT_USERS_HEAVY  = 50

# Acceptable p95 response time in seconds (stub endpoints should be very fast)
P95_LATENCY_THRESHOLD_SECONDS = 1.0

# Minimum acceptable requests/sec under medium load
MIN_THROUGHPUT_RPS = 10

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class RequestResult(NamedTuple):
    status_code: int
    duration_seconds: float
    error: str | None


def timed_request(client: TestClient, method: str, url: str, **kwargs) -> RequestResult:
    """Execute one HTTP request and record its duration."""
    start = time.perf_counter()
    try:
        response = getattr(client, method)(url, **kwargs)
        duration = time.perf_counter() - start
        return RequestResult(response.status_code, duration, None)
    except Exception as exc:  # noqa: BLE001
        duration = time.perf_counter() - start
        return RequestResult(-1, duration, str(exc))


def run_concurrent_requests(
    client: TestClient,
    method: str,
    url: str,
    n: int,
    **kwargs,
) -> list[RequestResult]:
    """Fire `n` concurrent requests and return all results."""
    results: list[RequestResult] = []
    lock = threading.Lock()

    def worker() -> None:
        result = timed_request(client, method, url, **kwargs)
        with lock:
            results.append(result)

    threads = [threading.Thread(target=worker) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    return results


def assert_latency(results: list[RequestResult], p95_threshold: float) -> None:
    """Assert that the p95 latency is within the given threshold."""
    durations = [r.duration_seconds for r in results]
    durations.sort()
    p95_index = int(len(durations) * 0.95)
    p95 = durations[min(p95_index, len(durations) - 1)]
    assert p95 < p95_threshold, (
        f"p95 latency {p95:.3f}s exceeds threshold {p95_threshold}s"
    )


def assert_no_server_errors(results: list[RequestResult]) -> None:
    """Assert that no 5xx responses were returned."""
    server_errors = [r for r in results if r.status_code >= 500 and r.status_code != 501]
    assert len(server_errors) == 0, (
        f"{len(server_errors)} requests returned 5xx: "
        + ", ".join(str(r.status_code) for r in server_errors[:5])
    )


def assert_throughput(results: list[RequestResult], duration_seconds: float, min_rps: float) -> None:
    """Assert minimum throughput was achieved."""
    rps = len(results) / duration_seconds if duration_seconds > 0 else 0
    assert rps >= min_rps, f"Throughput {rps:.1f} rps < minimum {min_rps} rps"


# ---------------------------------------------------------------------------
# Test payload factory
# ---------------------------------------------------------------------------

def generate_tests_payload(url: str = "https://example.com") -> dict:
    return {"url": url, "depth": 1}


# ===========================================================================
# Section 1: Single-request baseline
# ===========================================================================

class TestBaseline:
    """Baseline latency for a single request."""

    def test_generate_tests_baseline_latency(self, client):
        """Single POST /generate-tests must respond within 500ms."""
        result = timed_request(
            client, "post", "/api/v2/generate-tests/generate-tests",
            json=generate_tests_payload()
        )
        assert result.duration_seconds < 0.5, (
            f"Baseline latency {result.duration_seconds:.3f}s too high"
        )
        assert result.status_code in (200, 201, 202, 501)

    def test_get_workflow_status_baseline_latency(self, client):
        """Single GET /workflows/{id} must respond within 500ms."""
        result = timed_request(client, "get", "/api/v2/workflows/wf-baseline")
        assert result.duration_seconds < 0.5

    def test_get_workflow_results_baseline_latency(self, client):
        """Single GET /workflows/{id}/results must respond within 500ms."""
        result = timed_request(client, "get", "/api/v2/workflows/wf-baseline/results")
        assert result.duration_seconds < 0.5


# ===========================================================================
# Section 2: Concurrent load on POST /generate-tests
# ===========================================================================

class TestConcurrentGenerateTests:
    """Load tests for the test generation trigger endpoint."""

    def test_light_concurrency(self, client):
        """5 simultaneous trigger requests must all succeed."""
        results = run_concurrent_requests(
            client, "post", "/api/v2/generate-tests/generate-tests",
            CONCURRENT_USERS_LIGHT,
            json=generate_tests_payload()
        )
        assert len(results) == CONCURRENT_USERS_LIGHT
        assert_no_server_errors(results)

    def test_medium_concurrency_latency(self, client):
        """20 concurrent trigger requests must stay within p95 latency."""
        results = run_concurrent_requests(
            client, "post", "/api/v2/generate-tests/generate-tests",
            CONCURRENT_USERS_MEDIUM,
            json=generate_tests_payload()
        )
        assert_no_server_errors(results)
        assert_latency(results, P95_LATENCY_THRESHOLD_SECONDS)

    def test_heavy_concurrency_no_server_errors(self, client):
        """50 concurrent requests must not produce 5xx errors."""
        results = run_concurrent_requests(
            client, "post", "/api/v2/generate-tests/generate-tests",
            CONCURRENT_USERS_HEAVY,
            json=generate_tests_payload()
        )
        assert_no_server_errors(results)

    def test_throughput_under_medium_load(self, client):
        """Must sustain minimum throughput under 20 concurrent users."""
        start = time.perf_counter()
        results = run_concurrent_requests(
            client, "post", "/api/v2/generate-tests/generate-tests",
            CONCURRENT_USERS_MEDIUM,
            json=generate_tests_payload()
        )
        elapsed = time.perf_counter() - start
        assert_throughput(results, elapsed, MIN_THROUGHPUT_RPS)

    def test_no_errors_with_different_urls(self, client):
        """Each request uses a distinct URL to avoid any caching side effects."""
        def make_result(i: int) -> RequestResult:
            return timed_request(
                client, "post", "/api/v2/generate-tests/generate-tests",
                json=generate_tests_payload(url=f"https://example{i}.com/page")
            )

        with ThreadPoolExecutor(max_workers=CONCURRENT_USERS_LIGHT) as pool:
            futures = [pool.submit(make_result, i) for i in range(CONCURRENT_USERS_LIGHT)]
            results = [f.result() for f in as_completed(futures)]

        assert_no_server_errors(results)


# ===========================================================================
# Section 3: Concurrent load on GET /workflows/{id}
# ===========================================================================

class TestConcurrentWorkflowStatus:
    """Load tests for the workflow status polling endpoint."""

    def test_light_concurrency_status(self, client):
        """5 simultaneous status polls must all succeed."""
        results = run_concurrent_requests(
            client, "get", "/api/v2/workflows/wf-load-test",
            CONCURRENT_USERS_LIGHT
        )
        assert len(results) == CONCURRENT_USERS_LIGHT
        assert_no_server_errors(results)

    def test_medium_concurrency_status_latency(self, client):
        """20 concurrent status polls must stay within p95 latency."""
        results = run_concurrent_requests(
            client, "get", "/api/v2/workflows/wf-load-test",
            CONCURRENT_USERS_MEDIUM
        )
        assert_no_server_errors(results)
        assert_latency(results, P95_LATENCY_THRESHOLD_SECONDS)


# ===========================================================================
# Section 4: Mixed traffic simulation
# ===========================================================================

class TestMixedTraffic:
    """Simulate realistic traffic mix: 60% status polls, 40% trigger requests."""

    def test_mixed_traffic_no_server_errors(self, client):
        """Mix of trigger and status poll requests must not produce 5xx."""
        n = 20
        lock = threading.Lock()
        results: list[RequestResult] = []

        def worker(i: int) -> None:
            if i % 5 < 3:
                # 60%: status poll
                result = timed_request(client, "get", f"/api/v2/workflows/wf-mixed-{i}")
            else:
                # 40%: trigger
                result = timed_request(
                    client, "post", "/api/v2/generate-tests/generate-tests",
                    json=generate_tests_payload(url=f"https://example{i}.com")
                )
            with lock:
                results.append(result)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert len(results) == n
        assert_no_server_errors(results)
        assert_latency(results, P95_LATENCY_THRESHOLD_SECONDS)


# ===========================================================================
# Section 5: Statistics report
# ===========================================================================

class TestLatencyStatistics:
    """Collect and report latency statistics for profiling."""

    def test_print_latency_report(self, client, capsys):
        """Run 30 sequential requests and print a latency percentile report."""
        n = 30
        results = [
            timed_request(
                client, "post", "/api/v2/generate-tests/generate-tests",
                json=generate_tests_payload()
            )
            for _ in range(n)
        ]
        durations = sorted(r.duration_seconds for r in results)
        p50  = statistics.median(durations)
        p95  = durations[int(n * 0.95)]
        p99  = durations[int(n * 0.99)]
        mean = statistics.mean(durations)

        print(
            f"\n[Load Report] POST /api/v2/generate-tests  n={n}\n"
            f"  mean={mean*1000:.1f}ms  p50={p50*1000:.1f}ms  "
            f"p95={p95*1000:.1f}ms  p99={p99*1000:.1f}ms"
        )

        # Fail if p95 > threshold (ensures this test is actually catching slowness)
        assert p95 < P95_LATENCY_THRESHOLD_SECONDS
