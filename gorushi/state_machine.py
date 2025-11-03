
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
    attribution_qoute_char: str | None = None

    """
    This method is used for only testing purposes.
    """
    def process_string(self, s: str) -> str:
        tok: tuple[str,str] | None = None
        for c in s:
            tok = self.feed(c)

        if tok is None:
            return ""
        _, result = tok
        return result

    def flush_buffer(self) -> str:
        result = "".join(self.buffer)
        self.buffer = []
        return result

    def next_state(self, next_char: str) -> HTMLTokenizerState:
        tmp_buffer = [*self.buffer, next_char]
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
            elif (
                tmp_buffer[-2] == '=' and (next_char == '"' or next_char == "'")
            ):
                self.attribution_qoute_char = next_char
                return HTMLTokenizerState.ATTRIBUTE_OPEN
        elif self.state == HTMLTokenizerState.ATTRIBUTE_OPEN:
            if (
                tmp_buffer[-1] == self.attribution_qoute_char 
                and not tmp_buffer[-2] == '\\'
            ):
                return HTMLTokenizerState.TAG_OPEN
            else:
                return HTMLTokenizerState.ATTRIBUTE_OPEN
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
    ) -> tuple[str,str] | None:
        if from_state == HTMLTokenizerState.TAG_OPEN \
            and to_state == HTMLTokenizerState.SCRIPT_DATA:
            # Remove <script> from buffer
            self.buffer = self.buffer[:-8]
            return ("tag", "script")
        elif from_state == HTMLTokenizerState.TAG_OPEN \
            and to_state == HTMLTokenizerState.TEXT:
            # Remove <...> from buffer 
            content = "".join(self.buffer[1:-1]).strip()
            self.buffer = self.buffer[:-len(content)-2]
            return ("tag", content)
        elif from_state == HTMLTokenizerState.TEXT \
            and to_state == HTMLTokenizerState.TAG_OPEN:
            # Flush text before <
            content = "".join(self.buffer[:-1])
            self.buffer = self.buffer[-1:]
            return ("text", content)
        elif from_state == HTMLTokenizerState.COMMENT \
            and to_state == HTMLTokenizerState.TEXT:
            # Remove <!--...--> from buffer
            self.buffer = self.buffer
            return ("comment", "".join(self.buffer))
        elif from_state == HTMLTokenizerState.SCRIPT_DATA \
            and to_state == HTMLTokenizerState.TEXT:
            # Remove </script> from buffer
            self.buffer = self.buffer[:-9]
            return ("script", "".join(self.buffer))
        
        return None


    def feed(self, c: str) -> tuple[str,str] | None:
        next_state = self.next_state(c)
        self.buffer.append(c)

        result = self.trigger_action(self.state, next_state)

        self.state = next_state

        return result
