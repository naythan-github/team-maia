"""
ITGlue Regional URL Mapping

Maps ITGlue regions to their API base URLs.
"""

# Regional API endpoints
REGION_URLS = {
    'us': 'https://api.itglue.com',
    'eu': 'https://api.eu.itglue.com',
    'au': 'https://api.au.itglue.com',
}

# Default regions for instance types
DEFAULT_REGIONS = {
    'production': 'us',
    'sandbox': 'us',
}


def get_base_url(instance: str = 'sandbox', region: str = None) -> str:
    """
    Get ITGlue API base URL for instance and region.

    Args:
        instance: 'sandbox' or 'production'
        region: 'us', 'eu', or 'au' (auto-detected if None)

    Returns:
        Base URL for API requests

    Examples:
        >>> get_base_url('sandbox', 'au')
        'https://api.au.itglue.com'

        >>> get_base_url('production', 'eu')
        'https://api.eu.itglue.com'
    """
    # Use provided region or default
    if region is None:
        region = DEFAULT_REGIONS.get(instance, 'us')

    # Normalize region
    region = region.lower()

    # Get URL for region
    base_url = REGION_URLS.get(region)

    if not base_url:
        raise ValueError(
            f"Unknown region: {region}. "
            f"Valid regions: {', '.join(REGION_URLS.keys())}"
        )

    return base_url


def detect_region_from_url(url: str) -> str:
    """
    Detect region from ITGlue URL.

    Args:
        url: ITGlue URL (e.g., 'https://company.au.itglue.com')

    Returns:
        Region code ('us', 'eu', or 'au')

    Examples:
        >>> detect_region_from_url('https://company.au.itglue.com')
        'au'

        >>> detect_region_from_url('https://company.eu.itglue.com')
        'eu'
    """
    url_lower = url.lower()

    if '.au.itglue.com' in url_lower:
        return 'au'
    elif '.eu.itglue.com' in url_lower:
        return 'eu'
    else:
        return 'us'
