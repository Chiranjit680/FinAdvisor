import time
from collections import deque
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException
import os
from jose import jwt, JWTError
from dotenv import load_dotenv

load_dotenv()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

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
        # Define public paths that don't need authentication
        public_paths = [
            "/user/create_profile",
            "/user/token",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/"
        ]
        
        # Skip authentication for public paths
        path = request.url.path
        if any(path.startswith(public_path) for public_path in public_paths):
            return await call_next(request)
        
        # Check for Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                status_code=401,
                content="Authorization header missing or invalid.",
                media_type="text/plain"
            )
        
        # Extract and validate token
        token = auth_header.split(" ")[1]
        try:
            jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
        except jwt.PyJWTError:
            return Response(
                status_code=401,
                content="Invalid or expired token.",
                media_type="text/plain"
            )
            
        return await call_next(request)

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

