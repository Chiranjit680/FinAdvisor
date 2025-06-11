import time
from collections import deque
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException
import os
from jose import jwt, JWTError


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 1, period: int = 2):
        super().__init__(app)
        self.limit = limit        # Max requests
        self.period = period      # Time window (in seconds)
        self.req_timestamps = deque(maxlen=limit)

    async def dispatch(self, request: Request, call_next):
        current_time = time.time()

        # Remove old timestamps outside the rate window
        while self.req_timestamps and self.req_timestamps[0] < current_time - self.period:
            self.req_timestamps.popleft()

        if len(self.req_timestamps) >= self.limit:
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429
            )

        self.req_timestamps.append(current_time)

        response = await call_next(request)
        return response

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        token=request.headers.get("Authorization").split(" ")[1] if "Authorization" in request.headers else None
        if not token or not token.startswith("Bearer "):
            return Response(
                content="Authorization header missing or invalid.",
                status_code=401
            )
        else:
            payload=jwt.decode(
                token, 
                JWT_SECRET_KEY,
                algorithms=["HS256"]
            )
            if not payload:
                return Response(
                    content="Invalid token.",
                    status_code=401
                )
            if "sub" not in payload:
                return Response(
                    content="Token does not contain user information.",
                    status_code=401
                )
            request.state.user_id = payload["sub"]
        response = await call_next(request)
        return response
class LoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Log request details
        print(f"Request: {request.method} {request.url}")
        if request.headers:
            print(f"Headers: {request.headers}")

        response = await call_next(request)

        # Log response details
        print(f"Response status: {response.status_code}")
        return response
    
    