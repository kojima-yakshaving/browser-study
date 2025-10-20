from enum import Enum


class RenderMode(Enum):
    RAW = 1 
    RENDERED = 2


class RecognitionOutput(Enum):
    CONTINUE = 1
    FLUSH = 2
    FLUSH_AND_CONTINUE = 3


class EntityRecognizer:
    """
    recognizes entities in the given text
    """
    context: list[str]
    def __init__(self, context: list[str]):
        self.context = context 

    def _process(self, char: str) -> RecognitionOutput:
        # recognize entity patterns
        # ex. &gt; &lt;

        # Step 1: Check for starting character '&'
        if not self.context and char == "&":
            return RecognitionOutput.CONTINUE

        if self.context and char == "&": 
            return RecognitionOutput.FLUSH_AND_CONTINUE

        # Step 2: Check for 'g', 'l' after '&'
        if self.context and self.context[0] == "&":
            if char == 'g' or char == 'l': 
                return RecognitionOutput.CONTINUE 

        # Step 3: Check for 't' after '&g' or '&l'
        if char == 't': 
            if len(self.context) == 2 and self.context[0] == "&" and (self.context[1] == "g" or self.context[1] == "l"):
                return RecognitionOutput.CONTINUE

        if char == ";":
            return RecognitionOutput.FLUSH

        return RecognitionOutput.FLUSH

    def append(self, char: str):
        self.context.append(char)

    def recognize(self, char: str) -> RecognitionOutput:
        result = self._process(char)
        return result


    def flush(self) -> str:
        content = "".join(self.context)

        if content == "&gt;":
            content = ">"
        if content == "&lt;":
            content = "<"

        self.context.clear()

        return content

class Renderer:
    """
    renders contents of websites which is passed as a string
    """
    content: str
    render_mode: RenderMode

    def __init__(self, *, content: str, render_mode: RenderMode = RenderMode.RENDERED):
        self.content = content 
        self.render_mode = render_mode

    def render(self):
        if self.render_mode == RenderMode.RAW:
            print(self.content)
            return

        recognizer = EntityRecognizer([])
        result = RecognitionOutput.CONTINUE
        in_tag = False
        buffer = []
        for c in self.content:
            if c == "<":
                in_tag = True
            elif c == ">":
                in_tag = False
            elif not in_tag:
                result = recognizer.recognize(c)
                flushed = ""
                if result == RecognitionOutput.FLUSH:
                    recognizer.append(c)
                    flushed = recognizer.flush()
                    buffer.append(flushed)
                if result == RecognitionOutput.CONTINUE:
                    recognizer.append(c)
                    flushed = "" 
                if result == RecognitionOutput.FLUSH_AND_CONTINUE:
                    flushed = recognizer.flush()
                    recognizer.append(c)
                    buffer.append(flushed)

        flushed = recognizer.flush()
        buffer.append(flushed)

        print("".join(buffer))
        
