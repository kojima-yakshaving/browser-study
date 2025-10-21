import sys
from renderer import RenderMode, Renderer
from url import URL


def show(body, *, render_mode: RenderMode):
    print(
        Renderer(
            content = body, 
            render_mode = render_mode
        ).render()
    )

def load(url):
    body = url.request()
    show(body,  render_mode=RenderMode.RAW if url.show_raw else RenderMode.RENDERED)


if __name__ == "__main__":
    load(URL(sys.argv[1]))
