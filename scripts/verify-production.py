#!/usr/bin/env python3
"""Verify a deployed SafarMa V15 frontend and Belink AI backend.

Default checks do not invoke the AI model. Pass ``--privacy-smoke`` explicitly to
create one real analysis, export that temporary anonymous client's records, then
delete them and confirm deletion. The signed client token is never printed.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Literal


Edition = Literal["personal", "public"]


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8"))

    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


class VerificationError(RuntimeError):
    pass


def normalize_url(value: str, *, allow_path: bool = True) -> str:
    parsed = urllib.parse.urlparse(value.strip())
    local = parsed.hostname in {"localhost", "127.0.0.1"}
    if parsed.scheme != "https" and not (local and parsed.scheme == "http"):
        raise VerificationError(f"URL must use HTTPS: {value}")
    if not parsed.netloc or parsed.username or parsed.password:
        raise VerificationError(f"Invalid URL: {value}")
    if not allow_path and parsed.path.strip("/"):
        raise VerificationError(f"Origin must not contain a path: {value}")
    return value.rstrip("/")


def request(
    url: str,
    *,
    method: str = "GET",
    payload: Any | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = 30,
) -> Response:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request_headers = {"Accept": "application/json, text/html;q=0.9, */*;q=0.8", **(headers or {})}
    if body is not None:
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=request_headers, method=method)
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=context) as response:
            return Response(
                status=response.status,
                headers={key.lower(): value for key, value in response.headers.items()},
                body=response.read(),
            )
    except urllib.error.HTTPError as error:
        return Response(
            status=error.code,
            headers={key.lower(): value for key, value in error.headers.items()},
            body=error.read(),
        )
    except (urllib.error.URLError, TimeoutError) as error:
        raise VerificationError(f"Request failed for {url}: {error}") from error


def require(condition: bool, message: str) -> None:
    if not condition:
        raise VerificationError(message)


def print_check(label: str, detail: str = "OK") -> None:
    print(f"[PASS] {label}: {detail}")


def detect_edition(frontend: str) -> Edition:
    path = urllib.parse.urlparse(frontend).path.rstrip("/")
    return "public" if path.endswith("/public.html") or path.endswith("public.html") else "personal"


def frontend_base(frontend: str) -> str:
    parsed = urllib.parse.urlparse(frontend)
    path = parsed.path
    if path.endswith(".html"):
        path = path.rsplit("/", 1)[0] + "/"
    elif not path.endswith("/"):
        path += "/"
    return urllib.parse.urlunparse((parsed.scheme, parsed.netloc, path, "", "", "")).rstrip("/")


def check_frontend(frontend: str) -> Edition:
    response = request(frontend, headers={"Accept": "text/html"})
    require(response.status == 200, f"Frontend returned HTTP {response.status}")
    html = response.text()
    edition = detect_edition(frontend)

    common_markers = (
        "SafarMa | سفرِ ما",
        "belink-runtime.js?v=15",
        "belink-client-runtime.js?v=15",
        "belink-connected-v2.js?v=8",
        "privacy-controls.js?v=3",
        "safarma-specialists-v8.js?v=15",
        "Content-Security-Policy",
    )
    for marker in common_markers:
        require(marker in html, f"Frontend is missing V15 release marker: {marker}")

    if edition == "public":
        for marker in ("public-mode.js?v=1", "manifest-public.webmanifest?v=15"):
            require(marker in html, f"Public edition is missing marker: {marker}")
        for personal_marker in ("تولدت مبارک، ساناز", "Happy birthday, Sanaz", "trabzon-preset.js"):
            require(personal_marker not in html, f"Public edition contains personal marker: {personal_marker}")
    else:
        for marker in ("trabzon-preset.js?v=2", "manifest.webmanifest?v=15", "تولدت مبارک، ساناز"):
            require(marker in html, f"Personal edition is missing marker: {marker}")

    print_check("Frontend V15 entry point", edition)

    base = frontend_base(frontend)
    assets: dict[str, str] = {
        "privacy controls": f"{base}/privacy-controls.js?v=3",
        "service worker": f"{base}/sw.js",
        "legal policy": f"{base}/legal.html",
        "pilot pricing": f"{base}/pricing.html",
    }
    if edition == "public":
        assets.update(
            {
                "public mode": f"{base}/public-mode.js?v=1",
                "manifest": f"{base}/manifest-public.webmanifest?v=15",
            }
        )
    else:
        assets.update(
            {
                "Trabzon preset": f"{base}/trabzon-preset.js?v=2",
                "manifest": f"{base}/manifest.webmanifest?v=15",
            }
        )

    for label, url in assets.items():
        asset = request(url, headers={"Accept": "*/*"})
        require(asset.status == 200, f"{label} returned HTTP {asset.status}")
        require(len(asset.body) > 30, f"{label} is unexpectedly empty")
        print_check(label)

    manifest = request(assets["manifest"]).json()
    expected_start = "./public.html?v=15" if edition == "public" else "./?v=15"
    require(manifest.get("start_url") == expected_start, f"Manifest start_url is not {expected_start}")
    print_check("Installed PWA start URL", expected_start)

    service_worker = request(assets["service worker"]).text()
    require("safarma-v15-public-personal" in service_worker, "Service worker is not the unified V15 cache")
    require("public.html" in service_worker, "Service worker does not cache the public edition")
    require("pricing.html" in service_worker, "Service worker does not cache the public pricing page")
    print_check("Unified V15 service worker")
    return edition


def check_security_headers(response: Response) -> None:
    expected = {
        "cache-control": "no-store",
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "referrer-policy": "no-referrer",
    }
    for name, value in expected.items():
        actual = response.headers.get(name, "")
        require(value.casefold() in actual.casefold(), f"Missing or invalid {name}: {actual!r}")
    print_check("Backend security headers")


def check_backend(backend: str, frontend_origin: str) -> dict[str, Any]:
    health_response = request(f"{backend}/health")
    require(health_response.status == 200, f"/health returned HTTP {health_response.status}")
    check_security_headers(health_response)
    health = health_response.json()
    require(health.get("status") == "ok", "/health status is not ok")
    require(health.get("ai_connected") is True, "Production backend is not connected to OpenAI")
    require(health.get("persistent_session_secret") is True, "Persistent session secret is not active")
    require(health.get("client_isolation") == "signed", "Signed client isolation is not active")
    require(health.get("data_export") is True, "Data export is not reported as active")
    require(health.get("data_deletion") is True, "Data deletion is not reported as active")
    print_check("Backend health", f"version {health.get('version', 'unknown')}")

    ready_response = request(f"{backend}/ready")
    require(ready_response.status == 200, f"/ready returned HTTP {ready_response.status}")
    ready = ready_response.json()
    require(ready.get("status") == "ready", "Backend readiness status is not ready")
    require(ready.get("database") is True, "Backend database is not ready")
    print_check("Backend readiness")

    docs = request(f"{backend}/docs", headers={"Accept": "text/html"})
    require(docs.status == 404, f"Production API docs should be disabled; received HTTP {docs.status}")
    print_check("Production docs disabled")

    preflight = request(
        f"{backend}/api/belink-ai/analyze",
        method="OPTIONS",
        headers={
            "Origin": frontend_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,x-belink-client",
        },
    )
    require(preflight.status in {200, 204}, f"CORS preflight returned HTTP {preflight.status}")
    require(
        preflight.headers.get("access-control-allow-origin") == frontend_origin,
        f"CORS origin mismatch: {preflight.headers.get('access-control-allow-origin')!r}",
    )
    print_check("Production CORS", frontend_origin)
    return health


def privacy_smoke(backend: str) -> None:
    start = date.today() + timedelta(days=45)
    end = start + timedelta(days=5)
    profile = {
        "origin": "DOH",
        "destination_candidates": ["Trabzon", "Tbilisi"],
        "passport": "Iran",
        "residence_country": "Qatar",
        "residence_status": "gcc",
        "departure_date": start.isoformat(),
        "return_date": end.isoformat(),
        "travelers": 2,
        "budget_qar": 13500,
        "trip_style": ["nature", "relaxation"],
        "flight_preference": "prefer_direct",
        "accommodation": "4-star hotel",
        "transport_preference": "only if needed",
        "food_preference": "balanced",
        "halal_required": True,
        "language": "en",
    }
    analyzed = request(
        f"{backend}/api/belink-ai/analyze",
        method="POST",
        payload=profile,
        timeout=180,
    )
    require(analyzed.status == 200, f"Privacy smoke analysis returned HTTP {analyzed.status}: {analyzed.text()[:300]}")
    result = analyzed.json()
    token = result.get("client_token")
    require(isinstance(token, str) and token.startswith("b1."), "Analysis did not return a signed client identity")
    require(result.get("decision"), "Analysis did not return a decision")
    headers = {"X-Belink-Client": token}
    print_check("Temporary connected analysis", result.get("mode", "unknown"))

    exported = request(f"{backend}/api/belink-ai/user-data", headers=headers)
    require(exported.status == 200, f"Data export returned HTTP {exported.status}")
    export = exported.json()
    require(export.get("format") == "safarma-user-data-v1", "Unexpected export format")
    require(len(export.get("trips", [])) == 1, "Temporary export should contain exactly one trip")
    require(len(export.get("conversations", [])) == 1, "Temporary export should contain exactly one conversation")
    require("client_token" not in json.dumps(export), "Export unexpectedly contains a client token")
    print_check("Authenticated privacy export")

    deleted = request(f"{backend}/api/belink-ai/user-data", method="DELETE", headers=headers)
    require(deleted.status == 200, f"Data deletion returned HTTP {deleted.status}")
    receipt = deleted.json()
    require(receipt.get("deleted") is True, "Deletion receipt did not confirm deletion")
    print_check("Complete data deletion", json.dumps(receipt.get("records", {}), sort_keys=True))

    empty = request(f"{backend}/api/belink-ai/user-data", headers=headers)
    require(empty.status == 200, f"Post-deletion export returned HTTP {empty.status}")
    empty_data = empty.json()
    require(empty_data.get("trips") == [], "Trips remain after deletion")
    require(empty_data.get("conversations") == [], "Conversations remain after deletion")
    print_check("Post-deletion verification")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify a SafarMa V15 frontend edition and Belink AI production backend.")
    parser.add_argument(
        "--frontend",
        default="https://kmswp7ms8t-arch.github.io/SafarMa/public.html?v=15",
        help="SafarMa V15 personal or public URL",
    )
    parser.add_argument("--backend", required=True, help="Deployed Belink AI backend base URL")
    parser.add_argument(
        "--origin",
        default="https://kmswp7ms8t-arch.github.io",
        help="Expected browser Origin allowed by CORS",
    )
    parser.add_argument(
        "--privacy-smoke",
        action="store_true",
        help="Explicitly run one connected analysis, export its data, then delete it",
    )
    args = parser.parse_args()

    try:
        frontend = normalize_url(args.frontend)
        backend = normalize_url(args.backend)
        origin = normalize_url(args.origin, allow_path=False)
        edition = check_frontend(frontend)
        check_backend(backend, origin)
        if args.privacy_smoke:
            privacy_smoke(backend)
        else:
            print("[INFO] Paid/connected AI analysis was not invoked. Pass --privacy-smoke explicitly for an end-to-end disposable test.")
        print(f"\nSafarMa V15 {edition} production verification completed successfully.")
        return 0
    except VerificationError as error:
        print(f"[FAIL] {error}", file=sys.stderr)
        return 1
    except (ValueError, json.JSONDecodeError) as error:
        print(f"[FAIL] Invalid response: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
