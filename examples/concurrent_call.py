#!/usr/bin/env python3
"""
Concurrent caller for /api/v1/cluster/analyze.

Usage:
  python examples/concurrent_call.py \
    --url http://127.0.0.1:5000/api/v1/cluster/analyze \
    --concurrency 10 \
    --total-requests 10
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Concurrent API caller")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:5000/api/v1/cluster/analyze",
        help="Target API URL",
    )
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent workers")
    parser.add_argument("--total-requests", type=int, default=10, help="Total request count")
    parser.add_argument("--timeout", type=float, default=60.0, help="Per request timeout (s)")
    parser.add_argument(
        "--start-time",
        default="2026-01-13 09:00:00",
        help="start_time field",
    )
    parser.add_argument(
        "--end-time",
        default="2026-01-13 09:30:00",
        help="end_time field",
    )
    parser.add_argument(
        "--cluster-name",
        default="ga-lan-jdns1",
        help="cluster_name field",
    )
    return parser.parse_args()


def send_one(index: int, url: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        response = requests.post(url, json=payload, timeout=timeout)
        latency_ms = int((time.perf_counter() - started) * 1000)
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}
        return {
            "index": index,
            "ok": True,
            "status_code": response.status_code,
            "latency_ms": latency_ms,
            "request_id": body.get("request_id"),
            "body": body,
        }
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((time.perf_counter() - started) * 1000)
        return {
            "index": index,
            "ok": False,
            "status_code": None,
            "latency_ms": latency_ms,
            "request_id": None,
            "error": f"{type(exc).__name__}: {exc}",
        }


def main() -> None:
    args = parse_args()
    if args.concurrency <= 0:
        raise SystemExit("--concurrency must be > 0")
    if args.total_requests <= 0:
        raise SystemExit("--total-requests must be > 0")

    payload = {
        "start_time": args.start_time,
        "end_time": args.end_time,
        "cluster_name": args.cluster_name,
    }

    print("== Concurrent Call ==")
    print(f"url={args.url}")
    print(f"concurrency={args.concurrency}, total_requests={args.total_requests}")
    print(f"payload={json.dumps(payload, ensure_ascii=False)}")

    started = time.perf_counter()
    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        futures = [
            pool.submit(send_one, i, args.url, payload, args.timeout)
            for i in range(args.total_requests)
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            if result["ok"]:
                print(
                    f"#{result['index']:03d} status={result['status_code']} "
                    f"latency_ms={result['latency_ms']} request_id={result['request_id']}"
                )
            else:
                print(
                    f"#{result['index']:03d} ERROR latency_ms={result['latency_ms']} "
                    f"{result['error']}"
                )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    success = [r for r in results if r["ok"]]
    failed = [r for r in results if not r["ok"]]
    status_buckets: dict[int, int] = {}
    for r in success:
        code = r["status_code"]
        status_buckets[code] = status_buckets.get(code, 0) + 1

    print("\n== Summary ==")
    print(f"elapsed_ms={elapsed_ms}")
    print(f"success={len(success)}, failed={len(failed)}")
    print(f"status_buckets={status_buckets}")


if __name__ == "__main__":
    main()
