"""
Panel Response Cache Middleware
================================
Automatically caches successful panel API responses so the background
scheduler can include them in WebSocket broadcasts without re-computing.

Cached endpoints:
- /api/panel/pulse-v3/{symbol}  → panel:pulse_v3:{symbol}
- /api/panel/emel/{symbol}      → panel:emel:{symbol}
- /api/clear-trend/{symbol}     → panel:clear_trend:{symbol}
- /api/mtf/analysis?symbol=X    → panel:mtf:{symbol}
"""
from __future__ import annotations

import json
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from io import BytesIO

logger = logging.getLogger(__name__)

# Map URL patterns to cache keys
PANEL_ROUTES = {
    "/api/panel/pulse-v3/": "pulse_v3",
    "/api/panel/emel/": "emel",
    "/api/clear-trend/": "clear_trend",
}

PANEL_CACHE_TTL = 120  # 2 minutes


class PanelCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Only cache successful GET responses
        if request.method != "GET" or response.status_code != 200:
            return response

        path = request.url.path

        # Check if this is a panel route we want to cache
        panel_key = None
        symbol = None

        for route_prefix, key in PANEL_ROUTES.items():
            if path.startswith(route_prefix):
                panel_key = key
                # Extract symbol from path (last segment)
                symbol = path[len(route_prefix):].split("?")[0].strip("/")
                break

        # Special case: MTF analysis uses query param
        if path.startswith("/api/mtf/analysis"):
            panel_key = "mtf"
            symbol = request.query_params.get("symbol", "")

        if not panel_key or not symbol:
            return response

        # Read response body and cache it
        try:
            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            # Try to parse as JSON to verify it's valid
            try:
                data = json.loads(body)
                # Don't cache error responses
                if isinstance(data, dict) and data.get("error"):
                    return Response(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )
            except (json.JSONDecodeError, ValueError):
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type=response.media_type,
                )

            # Cache the response
            from services.redis_client import cache_set
            cache_key = f"panel:{panel_key}:{symbol.upper()}"
            cache_set(cache_key, data, ttl=PANEL_CACHE_TTL)

            # Return the response with the body we already read
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )
        except Exception as e:
            logger.debug(f"Panel cache middleware error: {e}")
            return response
