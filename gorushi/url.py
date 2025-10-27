class URL:
    scheme: str
    path: str 
    host: str
    port: int

    content: str | None = None

    view_source: bool = False
    
    def __init__(self, url: str):
        if url.startswith('view-source:'):
            self.view_source = True
            url = url[len('view-source:'):]

        if url.startswith("data:"):
            self.scheme = "data"
            content = url.split(",", 1)[1]
            self.content = content
            return

        tokens = url.split("://", 1)
        if len(tokens) == 1:
            # if scheme is not specified and starts with "/", assume file scheme
            if url.startswith("/"):
                self.scheme = "file"
            else:
                raise ValueError("Invalid URL: {}".format(url))
        else:
            self.scheme, url = url.split("://", 1)

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
