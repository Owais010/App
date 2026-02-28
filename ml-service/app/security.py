"""
Security middleware: API Key Authentication & Rate Limiting.

Configuration via environment variables:
    - API_KEY: Required API key (or comma-separated list)
    - RATE_LIMIT_REQUESTS: Max requests per window (default: 100)
    - RATE_LIMIT_WINDOW: Window size in seconds (default: 60)
"""

import os
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple, Optional, List

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


# =============================================================================
# API KEY AUTHENTICATION
# =============================================================================

class APIKeyAuth:
    """
    API Key authentication handler.
    
    Validates API keys from X-API-Key header.
    Can be disabled by not setting API_KEY env var.
    """
    
    def __init__(self):
        self.enabled = False
        self.valid_keys: List[str] = []
        self._load_config()
    
    def _load_config(self):
        """Load API keys from environment."""
        api_keys = os.getenv("API_KEY", "").strip()
        if api_keys:
            self.valid_keys = [k.strip() for k in api_keys.split(",") if k.strip()]
            self.enabled = len(self.valid_keys) > 0
            logger.info(f"API Key authentication {'enabled' if self.enabled else 'disabled'} "
                       f"({len(self.valid_keys)} keys configured)")
    
    def validate(self, api_key: Optional[str]) -> bool:
        """Validate an API key."""
        if not self.enabled:
            return True
        if not api_key:
            return False
        return api_key in self.valid_keys


api_key_auth = APIKeyAuth()


# =============================================================================
# RATE LIMITING
# =============================================================================

class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window.
    
    For production, use Redis-based rate limiting.
    """
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
        self.max_requests = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.window_seconds = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        self.enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        
        logger.info(f"Rate limiting {'enabled' if self.enabled else 'disabled'}: "
                   f"{self.max_requests} requests per {self.window_seconds}s")
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier for rate limiting."""
        # Use API key if present, otherwise IP
        api_key = request.headers.get("X-API-Key", "")
        if api_key:
            return f"key:{api_key[:8]}..."
        
        # Get IP from X-Forwarded-For or direct connection
        forwarded = request.headers.get("X-Forwarded-For", "")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        else:
            client_ip = request.client.host if request.client else "unknown"
        
        return f"ip:{client_ip}"
    
    def is_allowed(self, request: Request) -> Tuple[bool, int, int]:
        """
        Check if request is allowed under rate limit.
        
        Returns:
            Tuple of (allowed, remaining, reset_seconds)
        """
        if not self.enabled:
            return True, self.max_requests, 0
        
        client_id = self._get_client_id(request)
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean old requests
        self.requests[client_id] = [
            ts for ts in self.requests[client_id] if ts > window_start
        ]
        
        # Check limit
        current_count = len(self.requests[client_id])
        remaining = max(0, self.max_requests - current_count)
        
        if current_count >= self.max_requests:
            # Calculate reset time
            oldest = min(self.requests[client_id]) if self.requests[client_id] else now
            reset_seconds = int(oldest + self.window_seconds - now)
            return False, 0, max(1, reset_seconds)
        
        # Record request
        self.requests[client_id].append(now)
        return True, remaining - 1, 0
    
    def cleanup(self):
        """Cleanup old entries to prevent memory leak."""
        now = time.time()
        window_start = now - self.window_seconds
        
        for client_id in list(self.requests.keys()):
            self.requests[client_id] = [
                ts for ts in self.requests[client_id] if ts > window_start
            ]
            if not self.requests[client_id]:
                del self.requests[client_id]


rate_limiter = RateLimiter()


# =============================================================================
# SECURITY MIDDLEWARE
# =============================================================================

class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Combined security middleware handling authentication and rate limiting.
    """
    
    # Paths that skip authentication
    SKIP_AUTH_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/metrics"}
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # Skip auth for health/docs endpoints
        if path in self.SKIP_AUTH_PATHS:
            return await call_next(request)
        
        # API Key authentication
        if api_key_auth.enabled:
            api_key = request.headers.get("X-API-Key")
            if not api_key_auth.validate(api_key):
                logger.warning(f"Invalid API key from {request.client.host if request.client else 'unknown'}")
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Unauthorized",
                        "detail": "Invalid or missing API key"
                    },
                    headers={"WWW-Authenticate": "X-API-Key"}
                )
        
        # Rate limiting
        allowed, remaining, reset_seconds = rate_limiter.is_allowed(request)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {request.client.host if request.client else 'unknown'}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "TooManyRequests",
                    "detail": f"Rate limit exceeded. Try again in {reset_seconds} seconds."
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limiter.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds),
                    "Retry-After": str(reset_seconds)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
