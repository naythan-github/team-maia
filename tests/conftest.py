"""
Shared pytest fixtures and helpers for ServiceDesk ETL V2 test suites

This file provides API normalization helpers to bridge the gap between
test expectations and actual implementation APIs.

Author: ServiceDesk ETL V2 Team
Date: 2025-10-19
"""

def normalize_profiler_result(result):
    """
    Normalize profiler result to include 'status' key for easier testing

    Profiler returns: {tables, issues, circuit_breaker, summary}
    Tests expect: {status: success|error, ...}

    Args:
        result: Raw profiler result dict

    Returns:
        Normalized result with 'status' key added
    """
    if not isinstance(result, dict):
        return {'status': 'error', 'error': 'Invalid result type'}

    # Check circuit breaker
    if 'circuit_breaker' in result:
        if result.get('circuit_breaker', {}).get('should_halt', False):
            return {'status': 'error', **result}
        else:
            return {'status': 'success', **result}

    # Fallback: if we got tables back, assume success
    if 'tables' in result:
        return {'status': 'success', **result}

    return {'status': 'error', **result}


def normalize_cleaner_result(result):
    """
    Normalize cleaner result (already has 'status' key, but standardize format)

    Cleaner returns: {status, dates_converted, empty_strings_converted, ...}
    Tests expect: Same format

    Args:
        result: Raw cleaner result dict

    Returns:
        Normalized result (currently pass-through)
    """
    if not isinstance(result, dict):
        return {'status': 'error', 'error': 'Invalid result type'}

    # Cleaner already returns status, just validate
    if 'status' not in result:
        # Add status based on presence of error
        if 'error' in result:
            result['status'] = 'error'
        else:
            result['status'] = 'success'

    return result


def extract_profiler_issues(result):
    """
    Extract issues list from profiler result

    Args:
        result: Profiler result (normalized or raw)

    Returns:
        List of issues, or empty list if none
    """
    return result.get('issues', [])


def extract_circuit_breaker(result):
    """
    Extract circuit breaker decision from profiler result

    Args:
        result: Profiler result (normalized or raw)

    Returns:
        Circuit breaker dict with should_halt, reason, recommendation
    """
    default = {
        'should_halt': False,
        'reason': '',
        'recommendation': 'PROCEED'
    }
    return result.get('circuit_breaker', default)


def assert_profiler_success(result):
    """
    Assert profiler completed successfully

    Args:
        result: Profiler result (raw or normalized)

    Raises:
        AssertionError if profiler failed
    """
    normalized = normalize_profiler_result(result)
    circuit_breaker = extract_circuit_breaker(normalized)

    assert normalized['status'] == 'success', \
        f"Profiler failed: {normalized.get('error', 'unknown error')}"

    # Additional check: circuit breaker should not halt on success
    if circuit_breaker['should_halt']:
        raise AssertionError(
            f"Circuit breaker halted: {circuit_breaker['reason']} "
            f"(recommendation: {circuit_breaker['recommendation']})"
        )


def assert_cleaner_success(result):
    """
    Assert cleaner completed successfully

    Args:
        result: Cleaner result

    Raises:
        AssertionError if cleaner failed
    """
    normalized = normalize_cleaner_result(result)

    assert normalized['status'] == 'success', \
        f"Cleaner failed: {normalized.get('error', 'unknown error')}"
