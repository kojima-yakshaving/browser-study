import sys
from gorushi.renderer import RenderMode, Renderer
from gorushi.connection import Connection
from gorushi.url import URL


def show(body: str, *, render_mode: RenderMode):
    print(
        Renderer(
            content = body, 
            render_mode = render_mode
        ).render()
    )

def load(url: URL):
    connection = Connection(http_options={'http_version': '1.1'})
    body = connection.request(url=url)
    show(body,  render_mode=RenderMode.RAW if url.view_source else RenderMode.RENDERED)


if __name__ == "__main__":
    load(URL(sys.argv[1]))
