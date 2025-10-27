from dataclasses import dataclass
import tkinter

from gorushi.connection import Connection
from gorushi.constants import DEFAULT_HEIGHT, DEFAULT_WIDTH
from gorushi.renderer import RenderMode, Renderer
from gorushi.url import URL


@dataclass
class Browser:
    window: tkinter.Tk
    canvas: tkinter.Canvas

    def __init__(self):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=DEFAULT_WIDTH, 
            height=DEFAULT_HEIGHT
        )
        self.canvas.pack()

    def load(self, url: URL):
        connection = Connection(http_options={'http_version': '1.1'})
        body = connection.request(url=url)

        self.show(
            body, 
            render_mode=RenderMode.RAW if url.view_source 
            else RenderMode.RENDERED
        )

        self.canvas.create_rectangle(10, 20, 400, 300)
        self.canvas.create_oval(100, 100, 150, 150)
        self.canvas.create_text(200, 150, text="Hello, World!")

    def show(self, body: str, *, render_mode: RenderMode):
        print(
            Renderer(
                content = body, 
                render_mode = render_mode
            ).render()
        )
