import socket
import ssl

class URL:
    scheme: str
    path: str 
    host: str
    port: int
    
    def __init__(self, url: str):
        tokens = url.split("://", 1)
        if len(tokens) == 1:
            if url.startswith("/"):
                self.scheme = "file"
            else:
                raise ValueError("Invalid URL: {}".format(url))
        else:
            self.scheme, url = url.split("://", 1)
            print(self.scheme, url)
            # if scheme is not specified and starts with "/", assume file scheme

            assert self.scheme in ("http", "https", "file")

        if self.scheme == "file":
            if url.startswith("//"):
                url = url[2:]
            # if url not starts with "/", add it
            if not url.startswith("/"):
                url = "/" + url
            self.path = url
            return

        if "/" not in url:
            url = url + "/"
        self.host, url = url.split("/", 1)
        self.path = "/" + url

        if self.scheme == "http":
            self.port = 80
        elif self.scheme == "https":
            self.port = 443

        if ":" in self.host:
            self.host, port = self.host.split(":", 1)
            self.port = int(port)

    def request(self):
        if self.scheme == "file":
            return self._request_file()
        else:
            return self._request_http()

    
    def _request_file(self):
        with open(self.path, "r") as f:
            return f.read()

    def _request_http(self):
        s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP
        )
        s.connect((self.host, self.port))
        if self.scheme == "https":
            ctx = ssl.create_default_context()
            s = ctx.wrap_socket(s, server_hostname=self.host)

        request = "GET {} HTTP/1.1\r\n".format(self.path)
        request += "Host: {}\r\n".format(self.host)
        request += "Connection: close\r\n"
        request += "User-Agent: kokokokojima\r\n"

        request += "\r\n"
        s.send(request.encode("utf8"))

        response = s.makefile("r", encoding="utf8", newline="\r\n")

        statusline = response.readline()
        version, status, explanation = statusline.split(" ", 2)

        response_headers = {}
        while True:
            line = response.readline()
            if line == "\r\n": 
                break
            header, value = line.split(":", 1)
            response_headers[header.casefold()] = value.strip()

        assert "transfer-encoding" not in response_headers
        assert "content-encoding" not in response_headers


        content = response.read()
        s.close()

        return content
