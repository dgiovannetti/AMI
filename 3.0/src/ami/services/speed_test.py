"""
AMI 3.0 - Speed test: measure download throughput (Mbps) and compute tier (slow/medium/fast).
Runs in a separate thread; no PyQt dependency.

Timing excludes DNS/TLS/connect: the clock starts at the first byte of the *measured*
window (after optional TCP warmup). Total bytes read = warmup_mb + download_size_mb.
"""

import time
from typing import List, Optional, Tuple

import requests

_CHUNK = 524288  # 512 KiB
# Cloudflare and some CDNs block non-browser clients (403). Try fallbacks if primary fails.
_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
_SPEED_HEADERS = {
    "User-Agent": _BROWSER_UA,
    "Accept": "*/*",
    "Accept-Encoding": "identity",
}

# Large enough for warmup (20) + timed download (50) MB if user maxes settings
_DEFAULT_FALLBACK_URLS: List[str] = [
    "https://speed.hetzner.de/100MB.bin",
    "https://proof.ovh.net/files/100Mb.dat",
    "http://ipv4.download.thinkbroadband.com:8080/50MB.zip",
    "https://speed.cloudflare.com/__down?bytes=104857600",
]


def _run_speed_test_one_url(
    url: str,
    measure_bytes: int,
    warmup_left: int,
    req_timeout: tuple[float, float],
) -> Optional[float]:
    """Single URL attempt; returns Mbps or None."""
    measure_left = measure_bytes
    t0: Optional[float] = None
    bytes_measured = 0
    warmup_remaining = warmup_left

    with requests.get(url, stream=True, timeout=req_timeout, headers=_SPEED_HEADERS) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=_CHUNK):
            if not chunk:
                continue
            i = 0
            while i < len(chunk):
                if warmup_remaining > 0:
                    use = min(warmup_remaining, len(chunk) - i)
                    warmup_remaining -= use
                    i += use
                    continue
                if measure_left <= 0:
                    break
                if t0 is None:
                    t0 = time.perf_counter()
                use = min(measure_left, len(chunk) - i)
                bytes_measured += use
                measure_left -= use
                i += use
            if measure_left <= 0:
                break

    if t0 is None or bytes_measured <= 0:
        return None
    elapsed = time.perf_counter() - t0
    if elapsed <= 0:
        return None
    speed_mbps = (bytes_measured * 8) / (elapsed * 1_000_000)
    return round(speed_mbps, 2)


def run_speed_test(
    test_url: str,
    download_size_mb: float,
    timeout_seconds: int,
    tier_low_mbps: float,
    tier_high_mbps: float,
    warmup_mb: float = 0.0,
    fallback_urls: Optional[List[str]] = None,
) -> Tuple[Optional[float], Optional[str]]:
    """
    Download: first warmup_mb (not timed), then download_size_mb (timed from first byte).
    Tries test_url, then built-in fallbacks (unless fallback_urls is an empty list).
    Returns (speed_mbps, tier) or (None, None) if every URL fails.
    """
    if not test_url or not test_url.strip():
        return None, None
    measure_bytes = int(download_size_mb * 1024 * 1024)
    if measure_bytes <= 0:
        return None, None
    warmup_left = max(0, int(round(warmup_mb * 1024 * 1024)))
    connect_timeout = min(10, max(1, int(timeout_seconds)))
    read_timeout = int(timeout_seconds)
    req_timeout = (float(connect_timeout), float(read_timeout))

    candidates: List[str] = [test_url.strip()]
    if fallback_urls is None:
        for u in _DEFAULT_FALLBACK_URLS:
            if u not in candidates:
                candidates.append(u)
    else:
        for u in fallback_urls:
            u = (u or "").strip()
            if u and u not in candidates:
                candidates.append(u)

    for url in candidates:
        try:
            speed_mbps = _run_speed_test_one_url(url, measure_bytes, warmup_left, req_timeout)
            if speed_mbps is None:
                continue
            if speed_mbps < tier_low_mbps:
                tier = "slow"
            elif speed_mbps < tier_high_mbps:
                tier = "medium"
            else:
                tier = "fast"
            return speed_mbps, tier
        except Exception:
            continue
    return None, None
