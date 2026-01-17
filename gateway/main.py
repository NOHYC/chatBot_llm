# main.py
import os
import uuid
import logging
import time
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import StreamingResponse

from api.v1 import chat
from config import get_settings



def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure root logging once.
    - Avoid duplicate handlers when reload=True
    - Make uvicorn logs flow through the same root logger
    - Log to both console and file
    """
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(level)

    fmt = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # 1) Console log
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)
    root.addHandler(console_handler)

    # 2) File log (rotate)
    log_dir = os.getenv("LOG_DIR", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.getenv("LOG_FILE", os.path.join(log_dir, "app.log"))

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=1024 * 1024 * 1024,  # 1024MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)

    # Let uvicorn loggers propagate to root logger
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers.clear()
        uv_logger.setLevel(level)
        uv_logger.propagate = True


def _to_text(data: bytes | str | None) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return data.decode("utf-8", errors="replace")


def _one_line(s: str) -> str:
    # 로그 한 줄 유지(원문은 유지하되 개행만 이스케이프)
    return s.replace("\r", "\\r").replace("\n", "\\n")


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    Log per request with full request/response bodies (text).
    - method, path, status, duration_ms, client_ip, request_body, response_body
    """

    async def dispatch(self, request: Request, call_next):
        rid = uuid.uuid4().hex[:8]
        start = time.perf_counter()
        client_ip = request.client.host if request.client else "-"

        # ---- read request body (and restore so downstream can read it again) ----
        req_body_bytes = await request.body()
        req_text = _one_line(_to_text(req_body_bytes))

        #async def receive():
        #    return {"type": "http.request", "body": req_body_bytes, "more_body": False}

        # Starlette/FastAPI가 다시 body를 읽을 수 있게 복구
        #request._receive = receive  # type: ignore[attr-defined]

        logger_req = logging.getLogger("request")

        try:
            response = await call_next(request)
        except Exception:
            ms = (time.perf_counter() - start) * 1000.0
            logger_req.exception(
                'RID=%s REQ %s %s -> 500 (%.1fms) client=%s req="%s"',
                rid, request.method, request.url.path, ms, client_ip, req_text
            )
            raise

        header_ms = (time.perf_counter() - start) * 1000.0

        # ---- non-streaming: response.body is available ----
        resp_body = getattr(response, "body", None)
        if resp_body is not None:
            resp_text = _one_line(_to_text(resp_body))
            logger_req.info(
                'RID=%s REQ %s %s -> %s (%.1fms) client=%s req="%s" resp="%s"',
                rid,
                request.method,
                request.url.path,
                response.status_code,
                header_ms,
                client_ip,
                req_text,
                resp_text,
            )
            return response

        # ---- streaming: wrap iterator and log full response when stream completes ----
        if isinstance(response, StreamingResponse) and getattr(response, "body_iterator", None) is not None:
            original_iterator = response.body_iterator
            collected = bytearray()

            async def wrapped_iterator():
                try:
                    async for chunk in original_iterator:
                        # chunk can be bytes or str
                        if isinstance(chunk, str):
                            b = chunk.encode("utf-8", errors="replace")
                            collected.extend(b)
                            yield chunk
                        else:
                            collected.extend(chunk)
                            yield chunk
                finally:
                    total_ms = (time.perf_counter() - start) * 1000.0
                    resp_text2 = _one_line(_to_text(bytes(collected)))
                    logger_req.info(
                        'RID=%s REQ %s %s -> %s (headers=%.1fms total=%.1fms) client=%s req="%s" resp="%s"',
                        rid,
                        request.method,
                        request.url.path,
                        response.status_code,
                        header_ms,
                        total_ms,
                        client_ip,
                        req_text,
                        resp_text2,
                    )

            response.body_iterator = wrapped_iterator()
            return response

        # ---- fallback: unknown response type (no body) ----
        logger_req.info(
            'RID=%s REQ %s %s -> %s (%.1fms) client=%s req="%s" resp="<no-body>"',
            rid,
            request.method,
            request.url.path,
            response.status_code,
            header_ms,
            client_ip,
            req_text,
        )
        return response


# Configure logging
configure_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Soccer Chat API",
    description="API server for streaming soccer match commentary chat responses",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add request logging middleware (full request/response bodies)
app.add_middleware(RequestLogMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # 모든 출처 허용
    allow_credentials=True,
    allow_methods=["*"],    # 모든 메서드 허용
    allow_headers=["*"],    # 모든 헤더 허용
)

# Include routers
app.include_router(
    chat.router,
    prefix="/api/v1/chat",
    tags=["chat"],
)


@app.get("/")
async def root():
    return {"message": "Soccer Chat API Server", "version": "1.0.0", "docs": "/docs"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "soccer-chat-api"}


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_config=None,   # do not override our logging config
        access_log=False,  # we log ourselves
    )

