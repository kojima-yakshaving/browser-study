
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

    def next_state(self, next_char: str) -> HTMLTokenizerState:
        tmp_buffer = self.buffer[-10:] + [next_char]
        if self.state == HTMLTokenizerState.TEXT:
            if next_char == '<':
                return HTMLTokenizerState.TAG_OPEN
            else:
                return HTMLTokenizerState.TEXT
        elif self.state == HTMLTokenizerState.TAG_OPEN:
            if tmp_buffer[-4:] == list("<!--"):
                return HTMLTokenizerState.COMMENT
            elif tmp_buffer[-8:] == list("<script>"):
                return HTMLTokenizerState.SCRIPT_DATA
            elif next_char == '>':
                return HTMLTokenizerState.TEXT
        elif self.state == HTMLTokenizerState.COMMENT:
            if tmp_buffer[-3:] == list("-->"):
                return HTMLTokenizerState.TEXT
            else:
                return HTMLTokenizerState.COMMENT
        elif self.state == HTMLTokenizerState.SCRIPT_DATA:
            if tmp_buffer[-9:] == list("</script>"):
                return HTMLTokenizerState.TEXT
            else:
                return HTMLTokenizerState.SCRIPT_DATA

        return self.state

    def trigger_action(
        self, 
        from_state: HTMLTokenizerState, 
        to_state: HTMLTokenizerState
    ) -> None:
        if from_state == HTMLTokenizerState.TAG_OPEN \
            and to_state == HTMLTokenizerState.SCRIPT_DATA:
            # Remove <script> from buffer
            self.buffer = self.buffer[:-8]
        elif from_state == HTMLTokenizerState.COMMENT \
            and to_state == HTMLTokenizerState.TEXT:
            # Remove <!--...--> from buffer
            self.buffer = self.buffer[:-3]
        elif from_state == HTMLTokenizerState.SCRIPT_DATA \
            and to_state == HTMLTokenizerState.TEXT:
            # Remove </script> from buffer
            self.buffer = self.buffer[:-9]


    def process_char(self, c: str) -> None:
        next_state = self.next_state(c)
        self.buffer.append(c)

        self.trigger_action(self.state, next_state)

        self.state = next_state
