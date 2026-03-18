"""
AMI 3.0 - Speed test: measure download throughput (Mbps) and compute tier (slow/medium/fast).
Runs in a separate thread; no PyQt dependency.
"""

import time
from typing import Optional, Tuple

import requests


def run_speed_test(
    test_url: str,
    download_size_mb: float,
    timeout_seconds: int,
    tier_low_mbps: float,
    tier_high_mbps: float,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Download from test_url up to download_size_mb, measure throughput.
    Returns (speed_mbps, tier) or (None, None) on error.
    tier: 'slow' (< tier_low_mbps), 'medium' (between), 'fast' (>= tier_high_mbps).
    """
    if not test_url or not test_url.strip():
        return None, None
    url = test_url.strip()
    size_bytes = int(download_size_mb * 1024 * 1024)
    if size_bytes <= 0:
        return None, None
    try:
        start = time.perf_counter()
        downloaded = 0
        # Chunk size 512 KB for better throughput on fast links (2.5+ Gbps)
        with requests.get(url, stream=True, timeout=timeout_seconds) as r:
            r.raise_for_status()
            for chunk in r.iter_content(chunk_size=524288):
                if chunk:
                    downloaded += len(chunk)
                if downloaded >= size_bytes:
                    break
        elapsed = time.perf_counter() - start
        if elapsed <= 0 or downloaded <= 0:
            return None, None
        speed_mbps = (downloaded * 8) / (elapsed * 1_000_000)
        if speed_mbps < tier_low_mbps:
            tier = "slow"
        elif speed_mbps < tier_high_mbps:
            tier = "medium"
        else:
            tier = "fast"
        return round(speed_mbps, 2), tier
    except Exception:
        return None, None
