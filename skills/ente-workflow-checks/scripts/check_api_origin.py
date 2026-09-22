#!/usr/bin/env python3
"""Check which server an exercised client actually contacted, using a local HAR."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--har", type=Path, required=True)
    parser.add_argument("--expected-origin", required=True)
    parser.add_argument("--api-path-prefix", action="append", required=True)
    args = parser.parse_args()
    try:
        raw = args.har.read_bytes()
        result = check_requests(json.loads(raw), args.expected_origin, args.api_path_prefix)
        result["har_sha256"] = hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError, KeyError, TypeError) as error:
        result = {"status": "incomplete", "error": str(error)}
    print(json.dumps(result, indent=2))
    return {"pass": 0, "fail": 1, "incomplete": 2}[result["status"]]


def check_requests(har, expected_origin, path_prefixes):
    expected = origin(expected_origin)
    parsed = urlsplit(expected_origin)
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("expected-origin must contain only scheme, host and optional port")
    if not path_prefixes or any(not path.startswith("/") for path in path_prefixes):
        raise ValueError("Choose API path prefixes starting with /, using the actual operation being tested")
    entries = har["log"]["entries"]
    if not isinstance(entries, list):
        raise ValueError("HAR log.entries must be a list")
    relevant = []
    for entry in entries:
        url = entry["request"]["url"]
        path = urlsplit(url).path
        if any(path.startswith(prefix) for prefix in path_prefixes):
            relevant.append({"origin": origin(url), "path": path})
    wrong = [request for request in relevant if request["origin"] != expected]
    return {
        "status": "incomplete" if not relevant else "fail" if wrong else "pass",
        "expected_origin": expected, "matched_requests": len(relevant),
        "wrong_destinations": wrong,
        "limit": "Only the matching requests in this supplied capture are checked. Capture freshness, feature success and unexercised paths are not established. Headers, bodies and URL queries are never printed.",
    }


def origin(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Expected an HTTP(S) URL without embedded credentials")
    host = parsed.hostname.lower()
    if ":" in host:
        host = "[" + host + "]"
    port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
    return parsed.scheme + "://" + host + ":" + str(port)


if __name__ == "__main__":
    sys.exit(main())
