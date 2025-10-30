import tkinter.font


class FontMeasurer:
    cache: dict[tuple[float, str, str, str], dict[str, float]]

    def __init__(self):
        self.cache = {}

    def measure(self, font: tkinter.font.Font, text: str) -> float:
        key = (
            font.cget("size"),
            font.cget("weight"),
            font.cget("slant"),
            font.cget('family')
        )
        if key not in self.cache:
            self.cache[key] = {}

        if text in self.cache[key]:
            return self.cache[key][text]

        if len(text) == 1:
            self.cache[key][text] = font.measure(text)
            return self.cache[key][text]

        # if len(text) <= 10:
        #     self.cache[key][text] = font.measure(text)
        #     return self.cache[key][text]

        if text not in self.cache[key]:
            self.cache[key][text] = sum(
                self.measure(font, c) for c in text 
            )

        return self.cache[key][text]

font_measurer = FontMeasurer()
