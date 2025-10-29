from dataclasses import dataclass


@dataclass
class URL:
    scheme: str
    path: str 
    host: str
    port: int

    content: str | None = None

    view_source: bool = False

    @classmethod
    def parse(cls, url: str) -> "URL":
        view_source = False
        scheme = ""
        if url.startswith('view-source:'):
            view_source = True
            url = url[len('view-source:'):]

        if url.startswith("data:"):
            scheme = "data"
            content = url.split(",", 1)[1]
            return cls(
                scheme=scheme, 
                path="", 
                host="", 
                port=0, 
                content=content, 
                view_source=view_source
            )

        tokens = url.split("://", 1)
        if len(tokens) == 1:
            # if scheme is not specified and starts with "/", assume file scheme
            if url.startswith("/"):
                scheme = "file"
            else:
                raise ValueError("Invalid URL: {}".format(url))
        else:
            scheme, url = url.split("://", 1)

            assert scheme in ("http", "https", "file")

        if scheme == "file":
            if url.startswith("//"):
                url = url[2:]
            # if url not starts with "/", add it
            if not url.startswith("/"):
                url = "/" + url
            path = url
            return cls(
                scheme=scheme, 
                path=path, 
                host="", 
                port=0, 
                view_source=view_source
            )

        port = 0
        if "/" not in url:
            url = url + "/"
        host, url = url.split("/", 1)
        path = "/" + url

        if scheme == "http":
            port = 80
        elif scheme == "https":
            port = 443

        if ":" in host:
            host, port = host.split(":", 1)
            port = int(port)

        return cls(
            scheme=scheme, 
            path=path, 
            host=host, 
            port=port, 
            view_source=view_source
        )
        
