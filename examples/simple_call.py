#!/usr/bin/env python3
"""
Single request caller for /api/v1/cluster/analyze.

Usage:
  python examples/simple_call.py \
    --url http://127.0.0.1:5000/api/v1/cluster/analyze
"""

from __future__ import annotations

import argparse
import json
from typing import Any

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Single API caller")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:5000/api/v1/cluster/analyze",
        help="Target API URL",
    )
    parser.add_argument("--timeout", type=float, default=60.0, help="Request timeout (s)")
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


def main() -> None:
    args = parse_args()
    payload: dict[str, Any] = {
        "start_time": args.start_time,
        "end_time": args.end_time,
        "cluster_name": args.cluster_name,
    }

    print(f"url={args.url}")
    print(f"payload={json.dumps(payload, ensure_ascii=False)}")
    response = requests.post(args.url, json=payload, timeout=args.timeout)
    print(f"status={response.status_code}")

    try:
        print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    except ValueError:
        print(response.text)


if __name__ == "__main__":
    main()
