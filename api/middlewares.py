import time
from collections import deque
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import HTTPException

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limit: int = 10, period: int = 60):
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
