#!/usr/bin/env python3
"""
PMP Rate Limit Tester - Find Optimal API Timing

Tests different rate limiting strategies to find the fastest timing
that doesn't trigger API throttling.

Usage:
    python3 pmp_rate_limit_tester.py
"""

import sys
import time
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from pmp_oauth_manager import PMPOAuthManager


class PMPRateLimitTester:
    """Test API rate limits to find optimal timing"""

    def __init__(self):
        self.oauth_manager = PMPOAuthManager()
        self.base_url = self.oauth_manager.server_url
        self.results = []

    def fetch_json(self, endpoint: str, page: int, max_retries: int = 1) -> Tuple[Optional[Dict], bool, float]:
        """
        Fetch JSON with minimal retry - we want to detect throttling quickly.

        Returns:
            (data, was_throttled, response_time)
        """
        import requests

        start_time = time.time()
        throttled = False

        try:
            token = self.oauth_manager.get_valid_token()
            headers = {"Authorization": f"Zoho-oauthtoken {token}"}
            url = f"{self.base_url}{endpoint}"
            params = {'page': page}

            response = requests.get(url, headers=headers, params=params, timeout=(10, 30))
            elapsed = time.time() - start_time

            if response.status_code == 200:
                content = response.text

                # Check for HTML throttling page
                if content.strip().startswith('<') or '<!DOCTYPE' in content or '<html' in content.lower():
                    return (None, True, elapsed)

                try:
                    data = response.json()
                    if 'message_response' in data:
                        return (data['message_response'], False, elapsed)
                    return (data, False, elapsed)
                except ValueError:
                    # JSON parse error = likely throttled
                    return (None, True, elapsed)

            elif response.status_code == 429:
                # Explicit rate limit
                return (None, True, elapsed)
            else:
                return (None, False, elapsed)

        except Exception as e:
            elapsed = time.time() - start_time
            return (None, False, elapsed)

    def test_rate_limit(self, endpoint: str, endpoint_name: str,
                       delay_ms: int, num_requests: int = 50) -> Dict:
        """
        Test a specific delay timing.

        Args:
            endpoint: API endpoint to test
            endpoint_name: Display name
            delay_ms: Delay between requests in milliseconds
            num_requests: Number of requests to make (default: 50)

        Returns:
            Test results dict
        """
        print(f"\n{'='*80}")
        print(f"Testing: {endpoint_name}")
        print(f"Delay: {delay_ms}ms between requests")
        print(f"Requests: {num_requests}")
        print(f"{'='*80}")

        delay_sec = delay_ms / 1000.0
        successful = 0
        throttled = 0
        errors = 0
        response_times = []
        throttle_at_request = None

        start_time = time.time()

        for i in range(1, num_requests + 1):
            data, was_throttled, resp_time = self.fetch_json(endpoint, i)
            response_times.append(resp_time)

            if was_throttled:
                throttled += 1
                if throttle_at_request is None:
                    throttle_at_request = i
                print(f"   [{i}/{num_requests}] ⚠️  THROTTLED (response time: {resp_time:.2f}s)")
                # Stop immediately on throttling
                print(f"\n⚠️  THROTTLED at request {i}/{num_requests} - stopping test")
                break
            elif data:
                successful += 1
                total = data.get('total', 'N/A')
                if i % 10 == 0:
                    print(f"   [{i}/{num_requests}] ✅ Success (response time: {resp_time:.2f}s, total: {total})")
            else:
                errors += 1
                print(f"   [{i}/{num_requests}] ❌ Error (response time: {resp_time:.2f}s)")

            # Apply delay before next request (except after last)
            if i < num_requests and not was_throttled:
                time.sleep(delay_sec)

        total_time = time.time() - start_time
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        result = {
            'endpoint': endpoint_name,
            'delay_ms': delay_ms,
            'num_requests': num_requests,
            'successful': successful,
            'throttled': throttled,
            'errors': errors,
            'throttle_at_request': throttle_at_request,
            'total_time': total_time,
            'avg_response_time': avg_response_time,
            'requests_per_second': successful / total_time if total_time > 0 else 0,
            'was_throttled': throttled > 0
        }

        # Print summary
        print(f"\n📊 Test Results:")
        print(f"   Successful: {successful}/{num_requests}")
        print(f"   Throttled: {throttled}")
        print(f"   Errors: {errors}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Avg response time: {avg_response_time:.3f}s")
        print(f"   Requests/sec: {result['requests_per_second']:.2f}")

        if throttled > 0:
            print(f"   ⚠️  THROTTLED at request {throttle_at_request}")
            print(f"   ❌ Delay too aggressive - increase delay")
        else:
            print(f"   ✅ No throttling detected")
            print(f"   💡 Could try faster (lower delay)")

        return result

    def find_optimal_rate_limit(self, endpoint: str, endpoint_name: str):
        """
        Binary search to find optimal rate limit.

        Strategy:
        1. Start with conservative delay (1000ms)
        2. If no throttling, try faster (500ms, 250ms, 100ms, 50ms)
        3. If throttling, increase delay
        4. Find sweet spot
        """
        print("="*80)
        print("RATE LIMIT OPTIMIZATION - BINARY SEARCH")
        print("="*80)
        print(f"Endpoint: {endpoint_name}")
        print(f"Finding optimal delay between requests...")
        print()

        # Test progression: Conservative → Aggressive
        # We'll test until we find throttling, then back off
        test_delays = [
            1000,  # 1 second (very conservative)
            500,   # 0.5 seconds
            250,   # 0.25 seconds (current systemreport setting)
            100,   # 0.1 seconds
            50,    # 0.05 seconds
            25,    # 0.025 seconds
            10,    # 0.01 seconds (very aggressive)
        ]

        optimal_delay = None
        last_working_delay = None

        for delay_ms in test_delays:
            print(f"\n🔍 Testing {delay_ms}ms delay...")
            result = self.test_rate_limit(endpoint, endpoint_name, delay_ms, num_requests=50)
            self.results.append(result)

            if result['was_throttled']:
                print(f"\n🛑 Found throttling threshold at {delay_ms}ms")
                print(f"   Optimal delay: {last_working_delay}ms (previous working delay)")
                optimal_delay = last_working_delay
                break
            else:
                last_working_delay = delay_ms
                print(f"\n✅ {delay_ms}ms works - trying faster...")
                # Short pause between tests
                time.sleep(2)

        if optimal_delay is None:
            # We never hit throttling - even 10ms works!
            optimal_delay = test_delays[-1]
            print(f"\n🎉 Amazing! Even {optimal_delay}ms works without throttling")

        return optimal_delay

    def print_final_summary(self, optimal_delay: int):
        """Print final summary and recommendations"""
        print("\n" + "="*80)
        print("OPTIMIZATION COMPLETE")
        print("="*80)

        print(f"\n🎯 OPTIMAL RATE LIMITING:")
        print(f"   Delay between requests: {optimal_delay}ms")
        print(f"   Requests per second: ~{1000/optimal_delay:.2f}")
        print(f"   Requests per minute: ~{60000/optimal_delay:.0f}")

        # Calculate extraction time estimates
        print(f"\n⏱️  ESTIMATED EXTRACTION TIMES:")
        endpoints = {
            'All Patches': 5200,
            'Supported Patches': 365487,
            'All Systems': 3357,
            'Deployment Policies': 92,
            'Scan Details': 3357,
            'Installed Patches': 3506,
            'Missing Patches': 1694,
            'View Configurations': 229,
            'SoM Computers': 3484
        }

        total_requests = sum([(count + 24) // 25 for count in endpoints.values()])  # Pages (25 per page)

        for name, count in endpoints.items():
            pages = (count + 24) // 25
            time_sec = pages * (optimal_delay / 1000.0)
            time_min = time_sec / 60
            print(f"   {name}: {pages} pages = {time_min:.1f} min")

        total_time_sec = total_requests * (optimal_delay / 1000.0)
        total_time_min = total_time_sec / 60
        print(f"\n   📊 TOTAL: {total_requests} pages = {total_time_min:.1f} min ({total_time_min/60:.1f} hours)")

        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. Update extractors to use {optimal_delay}ms delay")
        print(f"   2. Add retry logic for occasional throttling")
        print(f"   3. Monitor first few pages for stability")

        # Code snippet
        print(f"\n📝 CODE UPDATE:")
        print(f"   Replace:")
        print(f"      time.sleep(0.25)  # 250ms")
        print(f"   With:")
        print(f"      time.sleep({optimal_delay/1000.0})  # {optimal_delay}ms - optimized via testing")


if __name__ == '__main__':
    print("PMP Rate Limit Tester")
    print("Finding optimal API request timing")
    print()

    tester = PMPRateLimitTester()

    # Test on Supported Patches endpoint (365K records - good for testing)
    optimal_delay = tester.find_optimal_rate_limit(
        "/api/1.4/patch/supportedpatches",
        "Supported Patches"
    )

    tester.print_final_summary(optimal_delay)

    print("\n✅ Testing complete!")
