import tkinter.font
from dataclasses import dataclass, field
from typing import Literal, final, override

from gorushi.command import DrawCommand, DrawRect, DrawText
from gorushi.constants import (
    DEFAULT_HEIGHT, DEFAULT_HORIZONTAL_PADDING, DEFAULT_HSTEP, DEFAULT_VERTICAL_PADDING, DEFAULT_VSTEP, DEFAULT_WIDTH
)
from gorushi.font_measure_cache import font_measurer
from gorushi.node import Element, Node, Text
from gorushi.parser import print_tree


FONT_CACHE: dict[
    tuple[float, str, str],
    tuple[tkinter.font.Font, tkinter.Label | None]
] = {}

SOFT_HYPHEN = "-"

PRE_TAG_INDENT = 20

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


BLOCK_ELEMENTS = [
    'html', 'body', 'article', 'section', 'nav', 'aside',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hgroup', 'header', 
    'footer', 'address', 'p', 'hr', 'pre', 'blockquote', 
    'ol', 'ul', 'menu', 'li', 'dl', 'dt', 'dd', 'figure',
    'figcaption', 'main', 'div', 'table', 'form', 'fieldset',
    'legend', 'details', 'summary'
]


@dataclass
class BaseLayout:
    display_list: list[tuple[float,float,str, tkinter.font.Font]] = field(default_factory=list)
    children: list['BaseLayout'] = field(default_factory=list)

    x: float = 0.0
    y: float = 0.0

    width: float = DEFAULT_WIDTH
    height: float = DEFAULT_HEIGHT

    hstep: float = DEFAULT_HSTEP
    vstep: float = DEFAULT_VSTEP

    is_ltr: bool = True

    def paint(self) -> list[DrawCommand]:
        return []

    def layout(self):
        pass


@dataclass 
class Layout(BaseLayout):
    node: Node | None = None 
    parent : BaseLayout | None = None
    previous: BaseLayout | None = None

    display_list: list[tuple[float,float,str, tkinter.font.Font]] = field(default_factory=list)


@final
@dataclass
class DocumentLayout(Layout):
    @override
    def layout(self):
        child = BlockLayout(
            node=self.node,
            parent=self,
            previous=None 
        )
        self.children.append(child)

        self.width = DEFAULT_WIDTH - 2*DEFAULT_HORIZONTAL_PADDING
        self.x = DEFAULT_HORIZONTAL_PADDING
        self.y = DEFAULT_VERTICAL_PADDING
        child.layout()
        self.height = child.height

        if self.node:
            print_tree(self.node)

    @override
    def paint(self) -> list[DrawCommand]:
        return []


@final
@dataclass 
class BlockLayout(Layout):
    cursor_x: float = DEFAULT_HSTEP
    cursor_y: float = DEFAULT_VSTEP + DEFAULT_VERTICAL_PADDING

    nodes: Node | None = None

    size: int = 12
    font_weight: Literal["normal", "bold"] = "normal"
    style: Literal["italic", "roman"] = "roman"

    buffer_line: BufferLine = field(default_factory=BufferLine)

    pre_tag_depth: int = 0

    small_caps: bool = False


    def layout_mode(self) -> str:
        if isinstance(self.node, Text):
            return "inline"
        elif self.node and any(
            [isinstance(child, Element) and \
            child.tag in BLOCK_ELEMENTS
            for child in self.node.children if self.node]
        ):
            return 'block'
        elif self.node and self.node.children:
            return 'inline'

        return "block"

    @override
    def layout(self) -> None:
        # Setup x, y, width
        if self.previous:
            self.y = self.previous.y + self.previous.height
        else:
            if self.parent:
                self.y = self.parent.y

        if self.parent:
            self.x = self.parent.x
            self.width = self.parent.width

        # Determine layout mode
        mode = self.layout_mode()

        # Perform layout
        if mode == "block":
            previous = None
            if self.node is None:
                return 
            for child in self.node.children:
                next_child = BlockLayout(
                    node = child,
                    parent = self,
                    previous = previous 
                )
                self.children.append(next_child)
                previous = next_child
        else:
            self.cursor_x = self.indented_horizontal_start()
            self.cursor_y = 0
            self.font_weight = "normal"
            self.style = "roman"
            self.size = 12 

            self.buffer_line = BufferLine()
            if self.node:
                self.recurse(self.node)
            self.flush()

        for child in self.children:
            child.layout()

        # Calculate height
        if mode == "block":
            total_height = 0.0
            for child in self.children:
                total_height += child.height
            self.height = total_height
        else:
            self.height = self.cursor_y

    @override
    def paint(self) -> list[DrawCommand]:
        cmds: list[DrawCommand] = []

        gray_stippled = "gray"

        # Draw background rectangles FIRST so they appear behind text
        if isinstance(self.node, Element) and self.node.tag == "pre":
            x1 = self.x
            y1 = self.y - self.height * 0.5
            x2 = x1 + self.width
            y2 = y1 + self.height
            rect = DrawRect(
                left=x1,
                top=y1,
                right=x2,
                bottom=y2,
                color=gray_stippled
            )
            cmds.append(rect)

        if (
            isinstance(self.node, Element)
            and self.node.tag == 'nav'
            and self.node.attributes.get("class") == "links"
        ):
            x1 = self.x
            y1 = self.y - self.height * 0.5
            x2 = x1 + self.width
            y2 = y1 + self.height
            rect = DrawRect(
                left=x1,
                top=y1,
                right=x2,
                bottom=y2,
                color=gray_stippled
            )
            cmds.append(rect)

        # Draw text AFTER background rectangles
        if self.layout_mode() == "inline":
            for x, y, word, font in self.display_list:
                left = x
                word_length = font_measurer.measure(font, word)
                right = left + word_length
                bottom  = y + font.metrics("linespace")
                cmds.append(
                    DrawText(
                        left=x,
                        right=right,
                        top=y,
                        bottom=bottom,
                        text=word,
                        font=font
                    )
                )

        return cmds           

    @property
    def interpolate_width(self) -> float:
        return self.width - 2 * self.hstep - 2 * DEFAULT_HORIZONTAL_PADDING * 2

    def indented_horizontal_start(self) -> float:
        if not self.is_ltr: 
            return self.hstep
        return self.hstep + (self.pre_tag_depth * PRE_TAG_INDENT)

    def recurse(self, tree: Node):
        if isinstance(tree, Text):
            if self.pre_tag_depth > 0:
                lines = tree.text.splitlines(keepends=True)
                for line in lines:
                    self.process_word(line)
                    if line.endswith('\n'):
                        self.flush()
            else:
                for word in tree.text.split():
                    self.process_word(
                        word if not self.small_caps else word.upper()
                    )

        elif isinstance(tree, Element):
            self.open_tag(tree.tag)
            for child in tree.children:
                self.recurse(child)
            self.close_tag(tree.tag)

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
            self.cursor_x = self.indented_horizontal_start()
        
        self.buffer_line.add_word(
            x=self.cursor_x,
            font=font,
            word=word,
        )
        self.cursor_x += w + font_measurer.measure(font, " ")

    def open_tag(self, tag: str):
        if tag == "i":
            self.style = "italic"
        elif tag == "b":
            self.font_weight = "bold"
        elif tag == "small":
            self.size -= 2 
        elif tag == "big":
            self.size += 4
        elif tag == "abbr":
            self.size -= 2
            self.small_caps = True 
        elif tag == 'sup':
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
        elif tag == "sub": 
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
        elif tag == 'br':
            self.flush()
            self.cursor_y += self.vstep
        elif tag == 'pre':
            self.flush()
            self.pre_tag_depth += 1
        elif tag == 'h1':
            self.flush()
            self.size = 24
            self.cursor_y += self.vstep
        elif tag == 'h2':
            self.flush()
            self.size = 20
            self.cursor_y += self.vstep 
        elif tag == 'h3':
            self.flush()
            self.size = 16
            self.cursor_y += self.vstep 
        elif tag == 'h4':
            self.flush()
            self.size = 14
            self.cursor_y += self.vstep
        pass 

    def close_tag(self, tag: str):
        if tag == "i":
            self.style = "roman"
        elif tag == "b":
            self.font_weight = "normal"
        elif tag == "small":
            self.size += 2
        elif tag == "big":
            self.size -= 4
        elif tag == "abbr":
            self.size += 2
            self.small_caps = False
        elif tag == 'sup':
            context = self.buffer_line.pop_context()
            self.size = int(context.restore_size)
        elif tag == 'sub':
            context = self.buffer_line.pop_context()
            self.size = int(context.restore_size)
        elif tag == "p":
            self.flush()
            self.cursor_y += self.vstep
        elif tag == 'pre':
            self.flush()
            self.pre_tag_depth = max(0, self.pre_tag_depth - 1)
        elif tag == 'blockqoute':
            self.flush()
            self.cursor_y += self.vstep
        elif tag == 'h1':
            self.flush()
            self.size = 12
            self.cursor_y += self.vstep
        elif tag == 'h2':
            self.flush()
            self.size = 12
            self.cursor_y += self.vstep 
        elif tag == 'h3':
            self.flush()
            self.size = 12
            self.cursor_y += self.vstep
        elif tag == 'h4':
            self.flush()
            self.size = 12
            self.cursor_y += self.vstep

    def flush(self):
        if self.buffer_line.is_empty(): 
            return

        upper_bound, lower_bound = self.buffer_line.calculate_bounds()
        baseline = self.y + self.cursor_y + upper_bound

        for (rel_x, relative_y, word, font) in self.buffer_line.words:
            x = self.x + rel_x
            y = baseline + relative_y
            self.display_list.append(
                (x, y, word, font)
            )

        line_height = upper_bound - lower_bound
        self.cursor_y += int(line_height)
        self.cursor_x = self.indented_horizontal_start()

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


def paint_tree(
    layout_object: BaseLayout, 
    display_list: list[DrawCommand]
) -> None:
    display_list.extend(layout_object.paint())

    for child in layout_object.children:
        paint_tree(child, display_list)
