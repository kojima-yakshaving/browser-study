import tkinter.font
from dataclasses import dataclass, field
from typing import Literal

from gorushi.constants import (
    DEFAULT_HEIGHT, DEFAULT_HORIZONTAL_PADDING, DEFAULT_HSTEP, DEFAULT_VSTEP, DEFAULT_WIDTH
)
from gorushi.font_measure_cache import font_measurer
from gorushi.node import Tag, Text

FONT_CACHE: dict[
    tuple[float, str, str],
    tuple[tkinter.font.Font, tkinter.Label | None]
] = {}

@dataclass
class Layout:
    cursor_x: float = DEFAULT_HSTEP
    cursor_y: float = DEFAULT_VSTEP

    width: float = DEFAULT_WIDTH
    height: float = DEFAULT_HEIGHT

    hstep: float = DEFAULT_HSTEP 
    vstep: float = DEFAULT_VSTEP

    size: int = 12

    font_weight: Literal["normal", "bold"] = "normal"
    style: Literal["italic", "roman"] = "roman"

    display_list: list[tuple[float,float,str, tkinter.font.Font]] = field(default_factory=list)
    line: list[tuple[float, str, tkinter.font.Font]] = field(default_factory=list)

    @property
    def interpolate_width(self) -> float:
        return self.width - 2 * self.hstep - 2 * DEFAULT_HORIZONTAL_PADDING * 2

    def lex(self, body: str):
        out: list[Tag | Text] = []

        buffer = ""
        in_tag = False

        for c in body:
            if c == "<":
                in_tag = True
                if buffer:
                    out.append(Text(buffer))
                buffer = ""
            elif c == ">":
                in_tag = False
                out.append(Tag(buffer))
                buffer = ""
            else:
                buffer += c

        if not in_tag and buffer:
            out.append(Text(buffer))

        return out

    def process_word(self, word: str):
        font = self.get_font(self.size, self.font_weight, self.style)
        w = font_measurer.measure(font, word)

        if self.cursor_x + w > self.interpolate_width:
            self.flush()
            self.cursor_x = self.hstep

        
        self.line.append((self.cursor_x, word, font))
        self.cursor_x += w + font_measurer.measure(font, " ")

    def process_token(self, tok: Tag | Text):
        if isinstance(tok, Text):
            for word in tok.text.split():
                self.process_word(word)
        elif tok.tag == 'i': 
            self.style = "italic"
        elif tok.tag == '/i':
            self.style = "roman"
        elif tok.tag == 'b':
            self.font_weight = "bold"
        elif tok.tag == '/b':
            self.font_weight = "normal"
        elif tok.tag == "small":
            self.size -= 2
        elif tok.tag == "/small":
            self.size += 2
        elif tok.tag == "big":
            self.size += 4
        elif tok.tag == "/big":
            self.size -= 4
        elif tok.tag == "br":
            self.flush()
        elif tok.tag == "/p":
            self.flush()
            self.cursor_y += self.vstep
        elif tok.tag == "/blockqoute":
            self.flush()
            self.cursor_y += self.vstep
        elif tok.tag == "h1":
            self.flush()
            self.size = 24
            self.cursor_y += self.vstep
        elif tok.tag == "h2": 
            self.flush()
            self.size = 20
            self.cursor_y += self.vstep
        elif tok.tag == "h3": 
            self.flush()
            self.size = 16
            self.cursor_y += self.vstep
        elif tok.tag == "h4": 
            self.flush()
            self.size = 14
            self.cursor_y += self.vstep
        elif tok.tag == "/h1":
            self.size = 12
            self.flush()
            self.cursor_y += self.vstep
        elif tok.tag == "/h2":
            self.size = 12
            self.flush()
            self.cursor_y += self.vstep
        elif tok.tag == "/h3":
            self.size = 12
            self.flush()
            self.cursor_y += self.vstep
        elif tok.tag == "/h4":
            self.size = 12
            self.flush()
            self.cursor_y += self.vstep

    def flush(self):
        if not self.line: 
            return
        metrics = [font.metrics() for x, word, font in self.line]
        max_ascent = max([metric["ascent"] for metric in metrics])
        baseline = self.cursor_y + 1.15 * max_ascent

        for x, word, font in self.line:
            y = baseline - font.metrics("ascent")
            self.display_list.append((x, y, word, font))

        max_descent = max([metric["descent"] for metric in metrics])
        self.cursor_y = baseline + 1.15 * max_descent
        self.cursor_x = self.hstep
        self.line.clear()


    def get_font(self, 
        size: int, 
        weight: Literal['normal', 'bold'], 
        style: Literal['italic', 'roman']
    ) -> tkinter.font.Font:
        key = (size, weight, style)
        if key not in FONT_CACHE:
            font = tkinter.font.Font(
                family="Arial",
                size=size, 
                weight=weight,
                slant=style
            )
            # label = tkinter.Label(font=font)
            FONT_CACHE[key] = (font, None)
        return FONT_CACHE[key][0]

    def layout(self, tokens: list[Tag | Text]) -> \
        list[tuple[float,float,str, tkinter.font.Font]]:
        self.flush()
        for tok in tokens:
            self.process_token(tok)
        
        self.flush()

        return self.display_list
