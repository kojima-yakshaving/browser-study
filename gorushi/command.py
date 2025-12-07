from dataclasses import dataclass
from tkinter import Canvas
import tkinter
from tkinter.font import Font
from typing import override


@dataclass
class DrawCommand:
    top: float
    left: float
    bottom: float = 0.0
    right: float = 0.0

    def execute(self, _scroll: float, _canvas: Canvas) -> None:
        raise NotImplementedError()


@dataclass
class DrawText(DrawCommand):
    text: str = ""
    font: Font | None = None

    @override
    def execute(self, scroll: float, canvas: Canvas) -> None:
        assert self.font is not None
        _ = canvas.create_text(
            self.left,
            self.top - scroll,
            text=self.text,
            font=self.font,
            anchor="nw"
        )

@dataclass 
class DrawEmoji(DrawCommand):
    image: tkinter.PhotoImage | None = None

    @override
    def execute(self, scroll: float, canvas: Canvas) -> None:
        _ = canvas.create_image(
            self.left,
            self.top - scroll,
            image=self.image,
            anchor="nw"
        )

@dataclass
class DrawRect(DrawCommand):
    color: str = "black"

    def execute(self, scroll: float, canvas: Canvas) -> None:
        color, stipple = self.color.split('_') if '_' in self.color else (self.color, None)
        _ = canvas.create_rectangle(
            self.left,
            self.top - scroll,
            self.right,
            self.bottom - scroll,
            width=0,
            fill=color,
        )
