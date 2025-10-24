from typing import AsyncGenerator, Optional

import gzip

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

app = FastAPI(title="Browser Caching & Compression Testbed")

# Allow cross-origin requests from any origin so frontends can hit this test server freely.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def chunk_bytes(data: bytes, chunk_size: int = 16) -> AsyncGenerator[bytes, None]:
    """Yield compressed data in small chunks to resemble chunked transfer encoding."""
    for index in range(0, len(data), chunk_size):
        yield data[index : index + chunk_size]


@app.get("/cache")
async def cache_endpoint(mode: Optional[str] = None) -> PlainTextResponse:
    body = "Hello Cache"
    response = PlainTextResponse(body)
    if mode == "max-age":
        cache_value = "public, max-age=10"
    elif mode == "no-store":
        cache_value = "no-store"
    else:
        cache_value = "public, max-age=5"
    response.headers["Cache-Control"] = cache_value  # Controls how the browser caches this resource.
    response.headers["ETag"] = '"v1.0"'  # Static validator to test conditional requests.
    return response


@app.get("/gzip")
async def gzip_endpoint(request: Request):
    body = b"Hello GZip"
    accept_encoding = request.headers.get("accept-encoding", "")
    if "gzip" in accept_encoding.lower():
        compressed = gzip.compress(body)
        headers = {
            "Content-Encoding": "gzip",  # Tell the browser the payload is gzip-compressed.
        }
        return StreamingResponse(
            chunk_bytes(compressed),
            media_type="text/plain",
            headers=headers,
        )
    return PlainTextResponse(body.decode("utf-8"))


for i in reversed(range(21)):
    @app.get("/redirect/{i}")
    async def redirect_endpoint(i: int) -> JSONResponse:
        if i > 0:
            return JSONResponse(
                {"redirect": f"/redirect/{i - 1}"},
                status_code=302,
                headers={"Location": f"/redirect/{i - 1}"},
            )
        return JSONResponse({"message": "Final destination reached."})


@app.get("/headers")
async def headers_endpoint(request: Request) -> JSONResponse:
    # Expose all incoming headers for debugging requests from the custom browser.
    return JSONResponse(dict(request.headers))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Usage:
# uv run server.py
