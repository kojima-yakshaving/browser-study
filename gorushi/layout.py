import tkinter.font
from dataclasses import dataclass
from typing import Literal

from gorushi.constants import (
    DEFAULT_HEIGHT, DEFAULT_HORIZONTAL_PADDING, DEFAULT_HSTEP, DEFAULT_VSTEP, DEFAULT_WIDTH
)
from gorushi.node import Tag, Text


@dataclass
class Layout:
    cursor_x: float = DEFAULT_HSTEP
    cursor_y: float = DEFAULT_VSTEP

    width: float = DEFAULT_WIDTH
    height: float = DEFAULT_HEIGHT

    hstep: float = DEFAULT_HSTEP 
    vstep: float = DEFAULT_VSTEP

    font_weight: Literal["normal", "bold"] = "normal"
    style: Literal["italic", "roman"] = "roman"

    @property
    def interpolate_width(self) -> float:
        return self.width - 2 * self.hstep - 2 * DEFAULT_HORIZONTAL_PADDING * 2

    def process_token(self, token: Tag | Text):
        pass

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
                buffer += c
                out.append(Tag(buffer))
                buffer = ""
            else:
                buffer += c

        if not in_tag and buffer:
            out.append(Text(buffer))

        return out

    def layout(self, tokens: list[Tag | Text]) -> \
        list[tuple[float,float,str, tkinter.font.Font]]:
        for token in tokens:
            self.process_token(token)


        font = tkinter.font.Font()

        display_list: list[tuple[float,float,str,tkinter.font.Font]] = []
        cursor_x, cursor_y = self.hstep, self.vstep

        for tok in tokens:
            if isinstance(tok, Text):
                for word in tok.text.split():
                    font  = tkinter.font.Font(
                        size = 16,
                        weight = self.font_weight,
                        slant = self.style
                    )
                    w = font.measure(word)

                    if cursor_x + w > self.interpolate_width:
                        cursor_y += font.metrics("linespace") * 1.25
                        cursor_x = self.hstep

                        display_list.append((cursor_x, cursor_y, word, font))
                        cursor_x += w + font.measure(" ")
            elif tok.tag == 'i': 
                self.style = "italic"
            elif tok.tag == '/i':
                self.style = "roman"
            elif tok.tag == 'b':
                self.font_weight = "bold"
            elif tok.tag == '/b':
                self.font_weight = "normal"
                

        return display_list
