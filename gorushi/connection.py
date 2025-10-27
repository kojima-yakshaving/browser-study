from datetime import datetime
from io import BufferedReader
from socket import socket as Socket, AF_INET, SOCK_STREAM, IPPROTO_TCP
import ssl
from typing import ClassVar, Literal, NamedTuple, TypedDict

from gorushi.url import URL


class HttpOptions(TypedDict):
    http_version: Literal["1.0", "1.1"] | None


class ConnectionPoolCacheKey(NamedTuple):
    host: str 
    port: int


class BrowserCacheKey(NamedTuple):
    url: str


class BrowserCacheEntry(NamedTuple):
    content: str
    max_age: int
    timestamp: datetime | None = None


class Connection:
    """
    A connection to handle HTTP/HTTPS requests with support for connection pooling.
    """

    # Maximum number of redirects to follow
    #
    # See chromiums's implmentation: https://chromium.googlesource.com/chromium/src/+/refs/heads/main/net/url_request
    MAX_REDIRECTS = 20

    connection_pool: ClassVar[dict[ConnectionPoolCacheKey, Socket]] = {}
    browser_cache: ClassVar[dict[BrowserCacheKey, BrowserCacheEntry]] = {}

    socket: Socket | None
    http_options: HttpOptions

    def __init__(self, http_options: HttpOptions | None = None):
        self.socket = None 
        self.http_options = http_options or { "http_version": "1.0" }

    def _read_chunked_body(self, response: BufferedReader) -> bytes:
        body = b""
        while True:
            chunk_size_line = response.readline()
            chunk_size_str = chunk_size_line.split(b"\r\n")[0]
            chunk_size = int(chunk_size_str, 16)
            if chunk_size == 0:
                break
            chunk_data = response.read(chunk_size)
            body += chunk_data
            response.read(2)  # Read the trailing CRLF

        return body

    def _request_data(self, url: URL) -> str:
        return url.content or ""

    def _request_file(self, url: URL) -> str:
        with open(url.path, "r") as f:
            return f.read()

    def _request_http(self, url: URL, http_options: HttpOptions) -> str:
        now = datetime.now()
        browser_cache_key = BrowserCacheKey(url=str(url))

        # flush cache if expired
        if browser_cache_key in Connection.browser_cache:
            cached_content = Connection.browser_cache[browser_cache_key]
            age = (now - cached_content.timestamp).total_seconds() if cached_content.timestamp else 0
            if age >= cached_content.max_age:
                Connection.browser_cache.pop(browser_cache_key, None)
            else:
                return cached_content.content

        if http_options['http_version'] not in ("1.0", "1.1"):
            raise ValueError("Unsupported HTTP version")

        if http_options['http_version'] == '1.1': 
            key = ConnectionPoolCacheKey(host=url.host, port=url.port)
            if key in Connection.connection_pool:
                self.socket = Connection.connection_pool[key]
        
        response_headers = {}
        redirect_count = 0

        while True:
            if redirect_count > self.MAX_REDIRECTS:
                raise RuntimeError("Maximum redirect limit reached")

            if self.socket is None:
                self.socket = Socket(
                    family=AF_INET,
                    type=SOCK_STREAM,
                    proto=IPPROTO_TCP
                )

                self.socket.connect((url.host, url.port))
                if url.scheme == "https":
                    ctx = ssl.create_default_context()
                    self.socket = ctx.wrap_socket(self.socket, server_hostname=url.host)

            if http_options['http_version'] == "1.1":
                key = ConnectionPoolCacheKey(host=url.host, port=url.port)
                if key not in Connection.connection_pool:
                    Connection.connection_pool[key] = self.socket

            request = f"GET {url.path} HTTP/{http_options['http_version']}\r\n"
            request += f"Host: {url.host}\r\n"

            if http_options['http_version'] == "1.1":
                request += "Connection: keep-alive\r\n"
            elif http_options['http_version'] == "1.0":
                request += "Connection: close\r\n"
            request += "User-Agent: kokokokojima/1.0\r\n"
            request += "Accept-Encoding: *\r\n"
            request += "\r\n"

            self.socket.send(request.encode("utf-8"))

            response = self.socket.makefile("rb", encoding="utf-8", newline="\r\n")
            statusline = response.readline().decode("utf-8")
            version, status, explanation = statusline.split(" ", 2)

            response_headers: dict[str, str] = {}
            while True:
                line = response.readline().decode("utf-8")
                if line == "\r\n": 
                    break
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()

            if status.startswith("3") and 'location' in response_headers:
                if response_headers['location'].startswith("http://") or response_headers['location'].startswith("https://"):
                    # absolute redirect
                    url = URL(response_headers['location'])
                else:
                    # relative redirect
                    url = URL(url.scheme + "://" + url.host + f":{url.port}" + response_headers['location'])
                redirect_count += 1

                # Close the socket for HTTP/1.0 connections on redirect (not persistent)
                self.socket.close()
                self.socket = None
                continue 

            break

        content = ""
        if 'content-length' in response_headers:
            content_length = int(response_headers['content-length'])
            content = response.read(content_length).decode("utf-8")
        elif 'transfer-encoding' in response_headers and response_headers['transfer-encoding'].lower() == 'chunked':
            chunked_data = self._read_chunked_body(response)
            # Handle gzip encoding if present
            if 'content-encoding' in response_headers and response_headers['content-encoding'].lower() == 'gzip':
                import gzip
                decompressed_data = gzip.decompress(chunked_data)
                content = decompressed_data.decode("utf-8")
            else:
                content = chunked_data.decode("utf-8")
        else:
            content = response.read().decode("utf-8")

        if (
            http_options['http_version'] == "1.0" or 
            ('connection' in response_headers and response_headers['connection'].lower() == 'close')
        ):
            self.socket.close()
            self.socket = None 
            Connection.connection_pool.pop(ConnectionPoolCacheKey(host=url.host, port=url.port), None)


        if 'cache-control' in response_headers:
            cache_control = response_headers['cache-control']

            directives = [d.strip() for d in cache_control.split(",")]
            if "no-store" in directives:
                Connection.browser_cache.pop(BrowserCacheKey(url=str(url)), None)
                pass
            else:
                for directive in directives:
                    if not directive.startswith("max-age="):
                        continue

                    max_age = int(directive[len("max-age="):])
                    cached_content = Connection.browser_cache.get(BrowserCacheKey(url=str(url)))
                    if cached_content:
                        age = (datetime.now() - cached_content.timestamp).total_seconds() if cached_content.timestamp else 0
                        if age < cached_content.max_age:
                            content = cached_content.content 
                        else:
                            Connection.browser_cache[BrowserCacheKey(url=str(url))] = BrowserCacheEntry(
                                content=content,
                                max_age=max_age,
                                timestamp=datetime.now()
                            )
                    else:
                        Connection.browser_cache[BrowserCacheKey(url=str(url))] = BrowserCacheEntry(
                            content=content,
                            max_age=max_age,
                            timestamp=datetime.now()
                        )

        return content

    def request(self, *, url: URL) -> str:
        if url.scheme == "data":
            return self._request_data(url)
        elif url.scheme == "file":
            return self._request_file(url)
        else:
            return self._request_http(url,  http_options=self.http_options)

