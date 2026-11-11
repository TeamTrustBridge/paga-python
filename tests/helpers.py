"""Shared helpers for the paga-python test suite."""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional, Tuple

import httpx

from paga import PagaClient

PUBLIC_KEY = "PUBLIC-KEY"
SECRET_KEY = "SECRET-KEY"
HASH_KEY = "hashkey123"

COLLECT_BASE = "https://beta-collect.paga.com"
CHECKOUT_BASE = "https://beta-checkout.paga.com"
BUSINESS_BASE = "https://beta.mypaga.com/paga-webservices/business-rest/secured"


class Recorder:
    """Captures the requests a client makes and replays canned responses."""

    def __init__(self, responses: Optional[List[Tuple[int, Any]]] = None) -> None:
        self.requests: List[httpx.Request] = []
        self._responses = responses or []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self._responses:
            status, body = self._responses.pop(0)
        else:
            status, body = 200, {}
        return httpx.Response(status, json=body)

    @property
    def last(self) -> httpx.Request:
        assert self.requests, "no request was made"
        return self.requests[-1]

    @property
    def count(self) -> int:
        return len(self.requests)


def make_client(
    recorder: Recorder,
    **kwargs: Any,
) -> Tuple[PagaClient, httpx.AsyncClient]:
    """Build a client wired to the recorder's mock transport."""
    client = PagaClient(PUBLIC_KEY, SECRET_KEY, HASH_KEY, **kwargs)
    http = httpx.AsyncClient(transport=httpx.MockTransport(recorder.handler))
    client._http = http
    return client, http


def basic_credentials(request: httpx.Request) -> Tuple[str, str]:
    """Decode the HTTP Basic credentials off a request."""
    header = request.headers.get("authorization", "")
    assert header.startswith("Basic "), f"expected Basic auth, got {header!r}"
    decoded = base64.b64decode(header[len("Basic ") :]).decode("utf-8")
    username, _, password = decoded.partition(":")
    return username, password


def request_json(request: httpx.Request) -> Dict[str, Any]:
    """Decode a request's JSON body."""
    return json.loads(request.content.decode("utf-8"))
