from dataclasses import dataclass, field
import tkinter.font


@dataclass
class FontMeasurer:
    cache: dict[tuple[float, str, str, str], dict[str, float]] = field(default_factory=dict)
    fixed_cjk_width: dict[tuple[float, str, str, str], float] = field(default_factory=dict)

    def _font_key(self, font: tkinter.font.Font):
        return (
            font.cget("size"),
            font.cget("weight"),
            font.cget("slant"),
            font.cget("family"),
        )

    def _is_cjk(self, ch: str) -> bool:
        code = ord(ch)
        return (
            0x4E00 <= code <= 0x9FFF or  # Kanji
            0xAC00 <= code <= 0xD7A3 or  # Hangul
            0x3040 <= code <= 0x30FF or  # hiragana, katakana
            0x31F0 <= code <= 0x31FF or  # katakana extension
            0x3400 <= code <= 0x4DBF or  # CJK extension A
            0xFF00 <= code <= 0xFF60     # Fullwidth roman characters and halfwidth katakana
        )

    def _prefetch_ascii_widths(self, font: tkinter.font.Font, cache: dict[str, float]):
        """Prefetch widths for common ASCII characters."""
        ascii_chars = (
            [chr(i) for i in range(32, 127)]  # printable ASCII
        )
        for ch in ascii_chars:
            if ch not in cache:
                cache[ch] = font.measure(ch)

    def measure(self, font: tkinter.font.Font, text: str) -> float:
        if not text:
            return 0.0

        key = self._font_key(font)
        cache = self.cache.setdefault(key, {})

        # Prefetch widths for common ASCII characters (only once)
        if " " not in cache:
            self._prefetch_ascii_widths(font, cache)

        # Initialize fixed CJK width if not already done
        if key not in self.fixed_cjk_width:
            self.fixed_cjk_width[key] = font.measure("가")

        result = cache.get(text)
        if result is not None:
            return result

        # Single character case
        if len(text) == 1:
            if text not in cache:
                cache[text] = (
                    self.fixed_cjk_width[key]
                    if self._is_cjk(text)
                    else font.measure(text)
                )
            return cache[text]

        # Multi-character case
        width = 0.0
        for ch in text:
            w = cache.get(ch)
            if w is None:
                w = (
                    self.fixed_cjk_width[key]
                    if self._is_cjk(ch)
                    else font.measure(ch)
                )
                cache[ch] = w
            width += w

        cache[text] = width
        return width

font_measurer = FontMeasurer()
