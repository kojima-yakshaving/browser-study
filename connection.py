from socket import socket as Socket, AF_INET, SOCK_STREAM, IPPROTO_TCP
import ssl
from typing import ClassVar, Dict, Literal, NamedTuple, Optional, TypedDict

from url import URL


class HttpOptions(TypedDict):
    http_version: Optional[Literal["1.0", "1.1"]]


class ConnectionPoolCacheKey(NamedTuple):
    host: str 
    port: int


class Connection:
    connection_pool: ClassVar[Dict[ConnectionPoolCacheKey, Socket]] = {}

    socket: Optional[Socket]
    http_options: HttpOptions

    def __init__(self, http_options: Optional[HttpOptions] = None):
        self.socket = None 
        self.http_options = http_options or { "http_version": "1.0" }

    def _request_data(self, url: URL) -> str:
        return url.content or ""

    def _request_file(self, url: URL) -> str:
        with open(url.path, "r") as f:
            return f.read()

    def _request_http(self, url: URL, http_options: HttpOptions) -> str:
        if http_options['http_version'] not in ("1.0", "1.1"):
            raise ValueError("Unsupported HTTP version")

        if http_options['http_version'] == '1.1': 
            key = ConnectionPoolCacheKey(host=url.host, port=url.port)
            if key in Connection.connection_pool:
                self.socket = Connection.connection_pool[key]

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
        request += "\r\n"

        self.socket.send(request.encode("utf-8"))

        response = self.socket.makefile("r", encoding="utf-8", newline="\r\n")
        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": 
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        content = ""
        if 'content-length' in response_headers:
            content_length = int(response_headers['content-length'])
            content = response.read(content_length)
        else:
            content = response.read()

        if http_options['http_version'] == "1.0":
            self.socket.close()

        return content

    def request(self, *, url: URL) -> str:
        if url.scheme == "data":
            return self._request_data(url)
        elif url.scheme == "file":
            return self._request_file(url)
        else:
            return self._request_http(url,  http_options=self.http_options)

