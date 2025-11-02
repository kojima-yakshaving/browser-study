from time import time
import tkinter
import tkinter.font
from typing import ClassVar
import os

from gorushi.connection import Connection
from gorushi.constants import (
    DEFAULT_HEIGHT, DEFAULT_HORIZONTAL_PADDING, DEFAULT_HSTEP, DEFAULT_VERTICAL_PADDING, DEFAULT_VSTEP, DEFAULT_WIDTH
)
from gorushi.font_measure_cache import font_measurer
from gorushi.layout import Layout
from gorushi.renderer import aho_corasick_matcher
from gorushi.url import URL
from gorushi.node import Tag, Text

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
    scroll: float

    width: float
    height: float

    hstep: float = DEFAULT_HSTEP
    vstep: float = DEFAULT_VSTEP

    SCROLL_DOWN: ClassVar[int] = 100

    content: str = ""
    display_list: list[tuple[float,float,str,tkinter.font.Font]] = []

    scroll_height: float = 0

    is_ltr: bool
    center_align: bool = False

    def __init__(
        self,
        *,
        width: float = DEFAULT_WIDTH,
        height: float = DEFAULT_HEIGHT,
        is_ltr: bool = True,
        center_align: bool = False
    ):
        self.window = tkinter.Tk()
        self.canvas = tkinter.Canvas(
            self.window, 
            background="white",
            width=width, 
            height=height,
        )

        self.width = width
        self.height = height
        self.scroll = 0
        self.is_ltr = is_ltr
        self.center_align = center_align

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

        layout_instance = Layout(
            width = self.width,
            height = self.height,
            hstep = self.hstep,
            vstep = self.vstep,
        )
        tokens = layout_instance.lex(
            self.content,
        )
        self.display_list = layout_instance.layout(tokens)

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
        time_start = time()
        self.canvas.delete("all")

        drawable_words: list[tuple[float, float, str, tkinter.font.Font]] = []
        for x, y, word, font in self.display_list:
            # padding from bottom
            if y + DEFAULT_VERTICAL_PADDING + self.vstep > self.scroll + self.height:
                continue
            # padding from top
            if y - DEFAULT_VERTICAL_PADDING < self.scroll:
                continue
            drawable_words.append((x, y, word, font))

        alternative_drawable_words: list[tuple[float, float, str, tkinter.font.Font]] = []
        start_x = DEFAULT_HORIZONTAL_PADDING if self.is_ltr else self.width - DEFAULT_HORIZONTAL_PADDING

        emoji_positions: list[tuple[float, float, str]] = []
        for x, y, word, font in drawable_words:
            # calculrate exact positions of emojis in the word
            current_x = x
            for c in word:
                if c in emoji_map:
                    emoji_positions.append((current_x, y, c))
                    current_x += self.hstep
                else:
                    current_x += self.hstep

            alternative_word = [
                c if c not in emoji_map else " " for c in word
            ]
            alternative_drawable_words.append(
                (x, y, "".join(alternative_word), font)
            )

        line_width: dict[float, float] = {}
        for x, y, word, font in alternative_drawable_words:
            if y not in line_width:
                line_width[y] = 0
            line_width[y] += font_measurer.measure(font,word)
            line_width[y] += font_measurer.measure(font, " ")

        for x, y, word, font in alternative_drawable_words:
            x_pos: float = x + DEFAULT_HORIZONTAL_PADDING
            if not self.is_ltr:
                x_pos = start_x - (line_width[y]) + x - self.hstep - DEFAULT_HORIZONTAL_PADDING
            if self.center_align:
                x_pos = (self.width - line_width[y]) / 2 - DEFAULT_HORIZONTAL_PADDING + x

            replaced_word = aho_corasick_matcher.replace_all(word)
            _ = self.canvas.create_text(
                x_pos,
                y - self.scroll,
                text=replaced_word,
                font=font,
                fill="black",
                anchor="nw"
            )

        for x, y, c in emoji_positions:
            x_pos: float = x + DEFAULT_HORIZONTAL_PADDING
            if not self.is_ltr:
                x_pos = start_x - (line_width[y]) + x - self.hstep - DEFAULT_HORIZONTAL_PADDING
            if self.center_align:
                x_pos = (self.width - line_width[y]) / 2 - DEFAULT_HORIZONTAL_PADDING + x
            
            try:
                self.canvas.create_image(
                    x_pos,
                    y - self.scroll,
                    image=load_emoji_image(emoji_map[c]),
                    anchor="nw"
                )
            except Exception:
                _ = self.canvas.create_text(
                    x_pos,
                    y - self.scroll,
                    text=c,
                    anchor="nw"
                )

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

        end_time = time()
        print(f"Draw time: {end_time - time_start:.4f} seconds")


    def load(self, url: URL):
        body = ""
        if url.scheme != 'about':
            connection = Connection(http_options={'http_version': '1.1'})
            body = connection.request(url=url)
        else:
            body = ""
        self.content = body

        layout_instance = Layout(
            width = self.width,
            height = self.height,
            hstep = self.hstep,
            vstep = self.vstep,
            is_ltr = self.is_ltr,
        )
        tokens = layout_instance.lex(
            self.content, 
        )
        display_list = layout_instance.layout(tokens)

        cursor_y: float = display_list[-1][1] if display_list else 0
        self.scroll_height = cursor_y + DEFAULT_VERTICAL_PADDING + 2 * self.vstep

        self.draw()

