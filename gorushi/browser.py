from dataclasses import dataclass
import tkinter

from gorushi.connection import Connection
from gorushi.constants import (
    DEFAULT_HEIGHT, DEFAULT_HSTEP, DEFAULT_VSTEP, DEFAULT_WIDTH
)
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

        result = self.lex(
            body, 
            render_mode=RenderMode.RAW if url.view_source 
            else RenderMode.RENDERED
        )

        cursor_x, cursor_y = DEFAULT_HSTEP, DEFAULT_VSTEP
        for c in result: 
            _ = self.canvas.create_text(cursor_x, cursor_y, text=c)
            cursor_x += DEFAULT_HSTEP
            if cursor_x > DEFAULT_WIDTH - DEFAULT_HSTEP:
                cursor_x = DEFAULT_HSTEP
                cursor_y += DEFAULT_VSTEP

    def lex(self, body: str, *, render_mode: RenderMode):
        return Renderer(
            content = body, 
            render_mode = render_mode
        ).render()
