import sys
from renderer import RenderMode, Renderer
from connection import Connection
from url import URL


def show(body, *, render_mode: RenderMode):
    print(
        Renderer(
            content = body, 
            render_mode = render_mode
        ).render()
    )

def load(url):
    connection = Connection()
    body = connection.request(url=url)
    show(body,  render_mode=RenderMode.RAW if url.view_source else RenderMode.RENDERED)


if __name__ == "__main__":
    load(URL(sys.argv[1]))
