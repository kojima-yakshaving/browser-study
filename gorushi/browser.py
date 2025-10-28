import tkinter
from typing import ClassVar
import os

from gorushi.connection import Connection
from gorushi.constants import (
    DEFAULT_HEIGHT, DEFAULT_HSTEP, DEFAULT_VSTEP, DEFAULT_WIDTH
)
from gorushi.renderer import RenderMode, Renderer
from gorushi.url import URL

def get_project_root() -> str:
    import os
    # iterate until we find the project root (.git)
    parent = ""
    while True:
        if os.path.exists(os.path.join(parent, ".git")):
            break
        if os.path.abspath(parent) == os.path.abspath(os.path.join(parent, "..")):
            break
        parent = os.path.join(parent, "..")
    # resolve to absolute path 
    return os.path.abspath(parent)

project_root = get_project_root()

def build_emoji_map() -> dict[str, str]:
    """
    Build a mapping from emoji characters to their corresponding 
    image file paths.
    """
    emoji_map: dict[str, str] = {}
    openmoji_dir = os.path.join(project_root, "assets", "openmoji")

    if not os.path.exists(openmoji_dir):
        return emoji_map

    for filename in os.listdir(openmoji_dir):
        if not filename.endswith(".png"):
            continue

        # extract codepoint(s) from filename
        codepoint_str = filename[:-4]

        # process - multiple codepoints
        if "-" in codepoint_str:
            codepoints = [int(cp, 16) for cp in codepoint_str.split("-")]
            try:
                # combine codepoints into a single character
                char = "".join(chr(cp) for cp in codepoints)
                emoji_map[char] = os.path.join(openmoji_dir, filename)
            except (ValueError, OverflowError):
                pass
        else:
            # single codepoint
            try:
                codepoint = int(codepoint_str, 16)
                char = chr(codepoint)
                emoji_map[char] = os.path.join(openmoji_dir, filename)
            except (ValueError, OverflowError):
                pass

    return emoji_map


def load_emoji_image(file_path: str) -> tkinter.PhotoImage:
    """
    Load an emoji image from the given file path, using a cache to
    avoid reloading images multiple times.
    """
    if file_path in emoji_image_cache:
        return emoji_image_cache[file_path]
    
    try:
        image = tkinter.PhotoImage(
            file=file_path,
        )
        sampled_image = image.subsample(4) 
        emoji_image_cache[file_path] = sampled_image
        return image
    except tkinter.TclError:
        raise RuntimeError(f"Failed to load emoji image from {file_path}")


# Build the emoji map at module load time
emoji_map = build_emoji_map()

# Cache for loaded emoji images
emoji_image_cache: dict[str, tkinter.PhotoImage] = {}


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

    scroll_height: int = 0

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
        self.scroll = min(
            self.scroll + self.SCROLL_DOWN, 
            max(0, self.scroll_height - self.height)
        )
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        for x, y, c in self.display_list:
            if y > self.scroll + self.height:
                continue
            if y + self.vstep < self.scroll:
                continue

            # Draw emoji
            if c in emoji_map:
                try:
                    _ = self.canvas.create_image(
                        x,
                        y - self.scroll,
                        image=load_emoji_image(emoji_map[c]),
                    )
                except tkinter.TclError:
                    _ = self.canvas.create_text(x, y - self.scroll, text=c)
            else:
                _ = self.canvas.create_text(x, y - self.scroll, text=c)

        # Draw scrollbar
        if self.scroll_height > self.height:
            scrollbar_height = 30
            scrollbar_y = self.scroll * self.height // self.scroll_height
            _ = self.canvas.create_rectangle(
                self.width - 10, 
                scrollbar_y, 
                self.width, 
                scrollbar_y + scrollbar_height, 
                fill="blue"
            )

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

        self.scroll_height = cursor_y

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
