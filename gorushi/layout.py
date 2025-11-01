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

SOFT_HYPHEN = "-"


@dataclass 
class VerticalAlignContext:
    restore_size: float = 12.0
    relative_baseline_y: float = 0.0
    weight: Literal["normal", "bold"] = "normal"
    style: Literal["italic", "roman"] = "roman"


@dataclass 
class BufferLine:
    words: list[tuple[float, float, str, tkinter.font.Font]] = field(default_factory=list)
    baseline: float = 0.0
    current_baseline: float = 0.0

    context_stack: list[VerticalAlignContext] = field(default_factory=list)

    def clear(self):
        self.words.clear()

    def is_empty(self) -> bool:
        return len(self.words) == 0

    def reset(self):
        pass

    @property
    def previous_baseline(self) -> float:
        if not self.context_stack:
            return 0
        return self.context_stack[-1].relative_baseline_y

    def add_word(
        self, 
        *,
        x: float,
        font: tkinter.font.Font,
        word: str,
    ):
        self.words.append(
            (x, self.current_baseline - font.metrics("ascent"), word, font)
        )

    def calculate_bounds(self) -> tuple[float, float]:
        upper_bound = 0.0
        lower_bound = 0.0

        for _, y, __, font in self.words:
            metrics = font.metrics()
            ascent = metrics["ascent"]
            descent = metrics["descent"]
            if y + ascent > upper_bound:
                upper_bound = y + ascent
            if y - descent < lower_bound:
                lower_bound = y - descent

        return upper_bound, lower_bound

    def add_context(self, context: VerticalAlignContext):
        self.context_stack.append(context)
        self.current_baseline = context.relative_baseline_y

    def pop_context(self) -> VerticalAlignContext:
        if not self.context_stack:
            raise RuntimeError("No context to pop")

        context = self.context_stack.pop()
        if self.context_stack:
            self.current_baseline = self.context_stack[-1].relative_baseline_y
        else:
            self.current_baseline = 0.0

        return context


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
    buffer_line: BufferLine = field(default_factory=BufferLine)

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
            part = ""
            remainder = ""
            if len(word) >= 4:
                for i in range(3, len(word)):
                    part = word[:i] + SOFT_HYPHEN
                    part_width = font_measurer.measure(font, part)
                    if self.cursor_x + part_width > self.interpolate_width:
                        if i == 0:
                            # word is too long to fit in a single line
                            part = word
                            remainder = ""
                        else:
                            part = word[:i-1] + SOFT_HYPHEN
                            remainder = SOFT_HYPHEN + word[i-1:]
                        break
                if remainder:
                    self.buffer_line.add_word(
                        x=self.cursor_x,
                        font=font,
                        word=part,
                    )
                    word = remainder
            self.flush()
            self.cursor_x = self.hstep
        
        self.buffer_line.add_word(
            x=self.cursor_x,
            font=font,
            word=word,
        )
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
        elif tok.tag == 'sup':
            current_font = self.get_font(self.size, self.font_weight, self.style)
            metrics = current_font.metrics()
            ascent = metrics["ascent"]
            baseline_y = self.buffer_line.previous_baseline - int(ascent * 0.25)
            self.buffer_line.add_context(
                VerticalAlignContext(
                    restore_size=self.size,
                    relative_baseline_y=baseline_y,
                    weight=self.font_weight,
                    style=self.style
                )
            )
            previous_size = self.size
            self.size = int(previous_size * 0.75)
        elif tok.tag == '/sup':
            context = self.buffer_line.pop_context()
            self.size = int(context.restore_size)
        elif tok.tag == 'sub': 
            current_font = self.get_font(self.size, self.font_weight, self.style)
            metrics = current_font.metrics()
            descent = metrics["descent"]
            baseline_y = self.buffer_line.previous_baseline + int(descent * 0.25)
            self.buffer_line.add_context(
                VerticalAlignContext(
                    restore_size=self.size,
                    relative_baseline_y=baseline_y,
                    weight=self.font_weight,
                    style=self.style
                )
            )
            previous_size = self.size
            self.size = int(previous_size * 0.75)
        elif tok.tag == '/sub':
            context = self.buffer_line.context_stack.pop()
            self.size = int(context.restore_size)
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
        if self.buffer_line.is_empty(): 
            return

        upper_bound, lower_bound = self.buffer_line.calculate_bounds()
        baseline = self.cursor_y + upper_bound

        for (x, relative_y, word, font) in self.buffer_line.words:
            self.display_list.append((x, baseline + relative_y, word, font))

        line_height = upper_bound - lower_bound
        self.cursor_y += int(line_height)
        self.cursor_x = self.hstep

        self.buffer_line.clear()

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

    def reset(self):
        self.buffer_line.clear()
        self.buffer_line.reset()

    def layout(self, tokens: list[Tag | Text]) -> \
        list[tuple[float,float,str, tkinter.font.Font]]:
        self.reset()
        self.flush()

        for tok in tokens:
            self.process_token(tok)
        
        self.flush()

        return self.display_list
