
from dataclasses import dataclass, field
from enum import Enum


class HTMLTokenizerState(Enum):
    TEXT = 1 
    TAG_OPEN = 2 
    ATTRIBUTE_OPEN = 3 

    SCRIPT_DATA = 4

    COMMENT = 5


@dataclass
class HTMLTokenizerStateMachine:
    buffer: list[str] = field(default_factory=list)
    state: HTMLTokenizerState = HTMLTokenizerState.TEXT
    

    """
    This method is used for only testing purposes.
    """
    def process_string(self, s: str) -> None:
        for c in s:
            self.process_char(c)

    def flush_buffer(self) -> str:
        result = "".join(self.buffer)
        self.buffer = []
        return result

    def process_char(self, c: str) -> None:
        self.buffer.append(c)

        if self.state == HTMLTokenizerState.TEXT:
            if c == '<':
                self.state = HTMLTokenizerState.TAG_OPEN
        elif self.state == HTMLTokenizerState.TAG_OPEN:
            # Handle script tag start
            if self.buffer[-8:] == list("<script>"):
                self.state = HTMLTokenizerState.SCRIPT_DATA
                self.buffer = self.buffer[:-8]
            # Handle comment start
            elif self.buffer[-4:] == list("<!--"):
                self.state = HTMLTokenizerState.COMMENT
            elif c == '>':
                self.state = HTMLTokenizerState.TEXT 
        elif self.state == HTMLTokenizerState.COMMENT:
            if self.buffer[-3:] == list("-->"):
                self.state = HTMLTokenizerState.TEXT
                _ = self.flush_buffer()
        elif self.state == HTMLTokenizerState.SCRIPT_DATA:
            if self.buffer[-9:] == list("</script>"):
                self.state = HTMLTokenizerState.TEXT
                self.buffer = self.buffer[:-9]
