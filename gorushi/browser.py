import tkinter
from typing import ClassVar

from gorushi.connection import Connection
from gorushi.constants import (
    DEFAULT_HEIGHT, DEFAULT_HSTEP, DEFAULT_VSTEP, DEFAULT_WIDTH
)
from gorushi.renderer import RenderMode, Renderer
from gorushi.url import URL


class Browser:
    window: tkinter.Tk
    canvas: tkinter.Canvas
    scroll: int

    width: int
    height: int

    hstep: int = DEFAULT_HSTEP
    vstep: int = DEFAULT_VSTEP

    SCROLL_DOWN: ClassVar[int] = 100

    rendered_content: str = ""
    display_list: list[tuple[int,int,str]] = []

    def __init__(
        self,
        *,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT
    ):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            width=width, 
            height=height,
        )

        self.width = width
        self.height = height
        self.scroll = 0

        self.canvas.pack(
            expand=True,
            fill=tkinter.BOTH, 
        )
        
        _ = self.window.bind("<Down>", self.scrolldown)
        _ = self.window.bind("<Up>", self.scrollup)

        # Linux scroll events
        _ = self.window.bind("<Button-4>", self.scrollup)
        _ = self.window.bind("<Button-5>", self.scrolldown)

        _ = self.window.bind("<Configure>", self.resize)

    def resize(self, e: tkinter.Event) -> None:
        self.width = e.width
        self.height = e.height

        self.display_list = self.layout(self.rendered_content)

        self.draw()

    def scrollup(self, _: tkinter.Event) -> None:
        self.scroll = max(0, self.scroll - self.SCROLL_DOWN)
        self.draw()

    def scrolldown(self, _: tkinter.Event) -> None:
        self.scroll += self.SCROLL_DOWN
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.height: 
                continue
            if y + self.vstep < self.scroll: 
                continue
            _ = self.canvas.create_text(x, y - self.scroll, text=c)

    def layout(self,text: str) -> list[tuple[int, int, str]]:
        display_list: list[tuple[int,int,str]] = []
        cursor_x, cursor_y = self.hstep, self.vstep
        for c in text: 
            if c == '\n':
                cursor_x = self.hstep
                cursor_y += self.vstep
                continue
            display_list.append((cursor_x, cursor_y, c))
            _ = self.canvas.create_text(cursor_x, cursor_y, text=c)
            cursor_x += self.hstep
            if cursor_x > self.width - self.hstep:
                cursor_x = self.hstep
                cursor_y += self.vstep

        return display_list


    def load(self, url: URL):
        connection = Connection(http_options={'http_version': '1.1'})
        body = connection.request(url=url)

        self.rendered_content = self.lex(
            body, 
            render_mode=RenderMode.RAW if url.view_source 
            else RenderMode.RENDERED
        )

        # print(result)
        self.display_list = self.layout(self.rendered_content)

        self.draw()


    def lex(self, body: str, *, render_mode: RenderMode):
        return Renderer(
            content = body, 
            render_mode = render_mode
        ).render()
